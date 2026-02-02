from django.shortcuts import render
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json

@csrf_exempt  # Для POST-запросов от фронтенда (в продакшене используйте токены)
def signup_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Валидация данных
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            password2 = data.get('password2')
            
            # Проверка обязательных полей
            if not all([username, email, password, password2]):
                return JsonResponse({
                    'success': False,
                    'error': 'Все поля обязательны'
                }, status=400)
            
            # Проверка совпадения паролей
            if password != password2:
                return JsonResponse({
                    'success': False,
                    'error': 'Пароли не совпадают'
                }, status=400)
            
            # Проверка уникальности пользователя
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Пользователь с таким именем уже существует'
                }, status=400)
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Пользователь с таким email уже существует'
                }, status=400)
            
            # Создание пользователя
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Автоматический логин после регистрации
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': 'Регистрация успешна',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
            
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
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'error': 'Имя пользователя и пароль обязательны'
                }, status=400)
            
            # Аутентификация пользователя
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Вход выполнен успешно',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Неверное имя пользователя или пароль'
                }, status=401)
                
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