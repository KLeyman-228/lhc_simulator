from django.urls import path
from views import signup_view, logout_view, login_view, get_my_stats, get_leaderboard
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Профиль
    #path('profile/', get_profile, name='profile'),  # Профиль с рангом
    #path('profile/update/', update_profile, name='update_profile'),
    
    # Симуляции
    #path('simulations/', get_my_simulations, name='my_simulations'),  # История симуляций
    #path('simulations/run/', run_simulation, name='run_simulation'),
    
    # Статистика и рейтинг
    path('stats/', get_my_stats, name='my_stats'),  # Полная статистика
    path('leaderboard/', get_leaderboard, name='leaderboard'),  # Таблица лидеров
]
