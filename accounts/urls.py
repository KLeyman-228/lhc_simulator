from django.urls import path
import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Профиль
    path('profile/', views.get_profile, name='profile'),  # Профиль с рангом
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # Симуляции
    path('simulations/', views.get_my_simulations, name='my_simulations'),  # История симуляций
    path('simulations/run/', views.run_simulation, name='run_simulation'),
    
    # Статистика и рейтинг
    path('stats/', views.get_my_stats, name='my_stats'),  # Полная статистика
    path('leaderboard/', views.get_leaderboard, name='leaderboard'),  # Таблица лидеров
]
