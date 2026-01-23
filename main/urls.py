from django.urls import path
from main.views import get_inputs

urlpatterns = [
    #path('api/home/', home_api),
    #path('api/theory/', about_api),
    path('api/simulation/', get_inputs),
]