from django.urls import path
from .views import signup_view, login_view

urlpatterns = [
    path('api/signup/', signup_view, name='signup'),
    path('api/login/', login_view, name='login'),
    # ...
]