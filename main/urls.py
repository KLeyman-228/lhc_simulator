from django.urls import path
from main.views import get_inputs, csrf


urlpatterns = [
    #path('api/home/', home_api),
    #path('api/theory/', about_api),
    path('api/simulation/', get_inputs),
    path("api/csrf/", csrf),
    path("api/csrf", csrf),   # чтобы и без слеша работало
]
