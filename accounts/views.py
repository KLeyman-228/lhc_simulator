# accounts/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import F
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model

from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    LeaderboardSerializer,
    SimulationLogSerializer
)
from .models import SimulationLog

User = get_user_model()


# ========== РЕГИСТРАЦИЯ ==========

@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    """Регистрация нового пользователя"""
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Регистрация успешна!'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== ВХОД ==========

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Вход в аккаунт"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Укажите username и пароль'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response(
            {'error': 'Неверный username или пароль'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'user': UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'message': f'Добро пожаловать, {user.username}!'
    })


# ========== ПРОФИЛЬ С ПОЛНОЙ ИНФОРМАЦИЕЙ ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """
    Получить полный профиль текущего пользователя
    
    Возвращает:
    - Информацию о пользователе
    - Ранг в рейтинге
    - Статистику
    """
    user = request.user
    
    # Вычисляем ранг
    rank = User.objects.filter(rating_score__gt=user.rating_score).count() + 1
    total_users = User.objects.filter(simulation_count__gt=0).count()
    
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'simulation_count': user.simulation_count,
        'rating_score': user.rating_score,
        'last_simulation_time': user.last_simulation_time,
        'created_at': user.created_at,
        'rank': rank,
        'total_users': total_users
    })


# ========== ИСТОРИЯ СИМУЛЯЦИЙ ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_simulations(request):
    """
    Получить историю симуляций текущего пользователя
    
    Query параметры:
    - limit: количество записей (по умолчанию 10)
    """
    limit = int(request.GET.get('limit', 10))
    
    simulations = SimulationLog.objects.filter(
        user=request.user
    ).order_by('-created_at')[:limit]
    
    serializer = SimulationLogSerializer(simulations, many=True)
    
    return Response({
        'simulations': serializer.data,
        'total_count': SimulationLog.objects.filter(user=request.user).count()
    })


# ========== ПОЛНАЯ СТАТИСТИКА (ПРОФИЛЬ + СИМУЛЯЦИИ) ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_stats(request):
    """
    Получить полную статистику пользователя
    
    Возвращает:
    - Профиль
    - Ранг
    - Последние 10 симуляций
    """
    user = request.user
    
    # Ранг
    rank = User.objects.filter(rating_score__gt=user.rating_score).count() + 1
    total_users = User.objects.filter(simulation_count__gt=0).count()
    
    # Последние симуляции
    recent_simulations = SimulationLog.objects.filter(user=user).order_by('-created_at')[:10]
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'simulation_count': user.simulation_count,
            'rating_score': user.rating_score,
            'last_simulation_time': user.last_simulation_time,
            'created_at': user.created_at,
        },
        'rank': rank,
        'total_users': total_users,
        'recent_simulations': SimulationLogSerializer(recent_simulations, many=True).data
    })


# ========== ТАБЛИЦА ЛИДЕРОВ ==========

@api_view(['GET'])
def get_leaderboard(request):
    """
    Получить таблицу лидеров
    
    Query параметры:
    - limit: количество пользователей (по умолчанию 100)
    """
    limit = int(request.GET.get('limit', 100))
    
    users = User.objects.filter(
        simulation_count__gt=0
    ).order_by('-rating_score')[:limit]
    
    leaderboard = []
    for index, user in enumerate(users, start=1):
        leaderboard.append({
            'rank': index,
            'id': user.id,
            'username': user.username,
            'rating_score': user.rating_score,
            'simulation_count': user.simulation_count,
            'created_at': user.created_at
        })
    
    return Response({
        'leaderboard': leaderboard,
        'total_users': User.objects.filter(simulation_count__gt=0).count()
    })


# ========== ЗАПУСК СИМУЛЯЦИИ ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_simulation(request):
    """Запустить симуляцию и обновить рейтинг"""
    user = request.user
    simulation_type = request.data.get('simulation_type', 'proton_proton')
    energy = request.data.get('energy')
    duration = request.data.get('duration')
    simulation_results = request.data.get('simulation_results', [])  # ← ИСПРАВЛЕНО (убран пробел)
    
    # Расчет очков
    SIMULATION_POINTS = {
        'proton_proton': 10,
        'proton_neutron': 15,
        'quark_collision': 20,
    }
    base_points = SIMULATION_POINTS.get(simulation_type, 10)
    total_points = base_points
    
    # Обновление рейтинга
    User.objects.filter(pk=user.pk).update(
        simulation_count=F('simulation_count') + 1,
        rating_score=F('rating_score') + total_points,
        last_simulation_time=timezone.now()  # ← ИСПРАВЛЕНО (было last_simulation_time)
    )
    
    # Логирование
    simulation_log = SimulationLog.objects.create(
        user=user,
        simulation_type=simulation_type,
        energy=energy,
        duration=duration,
        simulation_results=simulation_results  # ← ИСПРАВЛЕНО (убран пробел)
    )
    
    user.refresh_from_db()
    
    # Новый ранг после симуляции
    new_rank = User.objects.filter(rating_score__gt=user.rating_score).count() + 1
    
    return Response({
        'success': True,
        'simulation_id': simulation_log.id,
        'simulation_count': user.simulation_count,
        'rating_score': user.rating_score,
        'points_earned': total_points,
        'rank': new_rank,
        'message': f'Симуляция завершена! +{total_points} очков'
    })


# ========== ОБНОВЛЕНИЕ ПРОФИЛЯ ==========

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Обновить профиль"""
    user = request.user
    username = request.data.get('username')
    email = request.data.get('email')
    
    if username and username != user.username:
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Этот username уже занят'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.username = username
    
    if email and email != user.email:
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Этот email уже используется'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.email = email
    
    user.save()
    
    return Response({
        'message': 'Профиль обновлен',
        'user': UserSerializer(user).data
    })


# ========== ВЫХОД ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Выход из аккаунта"""
    return Response({
        'success': True,
        'message': 'Выход выполнен успешно'
    })