from django.urls import path
from .views import signup_view, login_view, logout_view
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # ...
]