from django.shortcuts import render
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import F
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
import json

from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    LeaderboardSerializer,
    SimulationLogSerializer
)
from .models import SimulationLog

User = get_user_model()


@csrf_exempt  # Для POST-запросов от фронтенда (в продакшене используйте токены)
@permission_classes([AllowAny])
def signup_view(request):
    if request.method == 'POST':
        try:
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
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат JSON'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Метод не разрешен'
    }, status=405)



@csrf_exempt
@permission_classes([AllowAny])
def login_view(request):
    if request.method == 'POST':
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email or not password:
                return Response(
                    {'error': 'Укажите логин и пароль'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Аутентификация
            user = authenticate(username=email, password=password)
            
            if not user:
                return Response(
                    {'error': 'Неверный логин или пароль'},
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
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат JSON'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Метод не разрешен'
    }, status=405)

@csrf_exempt
@permission_classes([IsAuthenticated])
def logout_view(request):
    if request.method == 'POST':
        from django.contrib.auth import logout
        logout(request)
        return JsonResponse({
            'success': True,
            'message': 'Выход выполнен успешно'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Метод не разрешен'
    }, status=405)

def check_auth_view(request):
    """Проверка, авторизован ли пользователь"""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            }
        })
    else:
        return JsonResponse({
            'authenticated': False
        })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
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