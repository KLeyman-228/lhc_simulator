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

@api_view(['POST'])  # ← ДОБАВИЛИ ЭТО!
@permission_classes([AllowAny])
def signup_view(request):
    """Регистрация нового пользователя"""
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Создаем JWT токены
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Регистрация успешна! Добро пожаловать!'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== ВХОД ==========

@api_view(['POST'])  # ← ДОБАВИЛИ ЭТО!
@permission_classes([AllowAny])
def login_view(request):
    """Вход в аккаунт"""
    username = request.data.get('username')  # Или 'email' если логин по email
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Укажите username и пароль'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Аутентификация
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response(
            {'error': 'Неверный username или пароль'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Создаем токены
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'user': UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'message': f'Добро пожаловать, {user.username}!'
    })


# ========== ВЫХОД ==========

@api_view(['POST'])  # ← ДОБАВИЛИ ЭТО!
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Выход из аккаунта"""
    return Response({
        'success': True,
        'message': 'Выход выполнен успешно'
    })


# ========== ПРОВЕРКА АВТОРИЗАЦИИ ==========

@api_view(['GET'])  # ← ДОБАВИЛИ ЭТО!
@permission_classes([IsAuthenticated])
def check_auth_view(request):
    """Проверка, авторизован ли пользователь"""
    return Response({
        'authenticated': True,
        'user': UserSerializer(request.user).data
    })


# ========== ПРОФИЛЬ ==========

@api_view(['GET'])  # ← ДОБАВИЛИ ЭТО!
@permission_classes([IsAuthenticated])
def get_profile(request):
    """Получить профиль текущего пользователя"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


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


# ========== СИМУЛЯЦИИ И РЕЙТИНГ ==========

SIMULATION_POINTS = {
    'proton_proton': 10,
    'proton_neutron': 15,
    'quark_collision': 20,
}



@api_view(['POST'])  # ← ДОБАВИЛИ ЭТО!
@permission_classes([IsAuthenticated])
def run_simulation(request):
    """Запустить симуляцию и обновить рейтинг"""
    user = request.user
    simulation_type = request.data.get('simulation_type', 'proton_proton')
    energy = request.data.get('energy')
    duration = request.data.get('duration')
    simulation_results  = request.data.get('simulation_results ', [])
    
    # Расчет очков
    base_points = SIMULATION_POINTS.get(simulation_type, 10)
    total_points = base_points
    
    # Обновление рейтинга
    User.objects.filter(pk=user.pk).update(
        simulation_count=F('simulation_count') + 1,
        rating_score=F('rating_score') + total_points,
        last_simulation_time=timezone.now()
    )
    
    # Логирование
    SimulationLog.objects.create(
        user=user,
        simulation_type=simulation_type,
        energy=energy,
        duration=duration,
        simulation_results =simulation_results 
    )
    
    user.refresh_from_db()
    
    return Response({
        'success': True,
        'simulation_count': user.simulation_count,
        'rating_score': user.rating_score,
        'points_earned': total_points,
        'message': f'Симуляция завершена! +{total_points} очков'
    })


@api_view(['GET'])  # ← ДОБАВИЛИ ЭТО!
def get_leaderboard(request):
    """Получить топ пользователей"""
    limit = int(request.GET.get('limit', 100))
    
    users = User.objects.filter(
        simulation_count__gt=0
    ).order_by('-rating_score')[:limit]
    
    leaderboard = []
    for index, user in enumerate(users, start=1):
        user_data = LeaderboardSerializer(user).data
        user_data['rank'] = index
        leaderboard.append(user_data)
    
    return Response({'leaderboard': leaderboard})


@api_view(['GET'])  # ← ДОБАВИЛИ ЭТО!
@permission_classes([IsAuthenticated])
def get_my_stats(request):
    """Получить статистику пользователя"""
    user = request.user
    
    rank = User.objects.filter(rating_score__gt=user.rating_score).count() + 1
    recent_simulations = SimulationLog.objects.filter(user=user)[:10]
    
    return Response({
        'user': UserSerializer(user).data,
        'rank': rank,
        'total_users': User.objects.filter(simulation_count__gt=0).count(),
        'recent_simulations': SimulationLogSerializer(recent_simulations, many=True).data
    })