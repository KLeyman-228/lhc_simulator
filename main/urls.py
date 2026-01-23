from django.urls import path
from main.views import home_api, about_api

urlpatterns = [
    path('api/home/', home_api),
    path('api/theory/', about_api),
    path('api/simulation/', about_api),
]