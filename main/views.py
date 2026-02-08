from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from django.http import JsonResponse
from .LHC_Simulator import SimulationEvent, load_particles
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.utils import add_simulation_rating


# Глобальные переменные
Load_particle = False
particle_list = []
resonances = []  # ← Добавь эту переменную!

@require_GET
@ensure_csrf_cookie
def csrf(request):
    # Просто устанавливает csrftoken cookie
    return JsonResponse({"detail": "CSRF cookie set"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_inputs(request):
    try:
        data = request.data  # ✅ DRF сам парсит JSON и кэширует body
    except Exception as e:
        return JsonResponse({"error": f"Invalid JSON: {str(e)}"}, status=400)

    if not isinstance(data, list) or not data:
        return JsonResponse({"error": "Payload must be a non-empty list"}, status=400)

    inputs = data[0]

    try:
        result = Collide_Simulation(inputs)

        simulation_type = 'hadron-hadron'
        energy = 13
        
        # Запускаем симуляцию
        simulation_results = result
        
        # Добавляем рейтинг
        rating_update = add_simulation_rating(
            user=request.user,
            simulation_type=simulation_type,
            particles_detected=3,
            energy=energy,
            collision_results=simulation_results
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse(result, safe=False)


def LoadAll():
    """Загрузка частиц (один раз)"""
    
    global Load_particle, particle_list, resonances  # ← ВАЖНО! Объяви все глобальные переменные
    
    if Load_particle is False:
        # Загружаем частицы
        particle_list, resonances = load_particles()
        Load_particle = True
    
    return particle_list, resonances


def Collide_Simulation(options):
    """Симуляция столкновения"""
    
    # Загружаем частицы (если еще не загружены)
    particle_list, resonances = LoadAll()
    
    # Получаем параметры
    id_1 = options.get('id_1')
    id_2 = options.get('id_2')
    E = options.get('Energy')
    
    # Проверка входных данных
    if id_1 is None or id_2 is None or E is None:
        raise ValueError("Missing required parameters: id_1, id_2, Energy")
    
    # Симуляция
    finals, first_finals, values = SimulationEvent(
        id_1, id_2, E, particle_list, resonances
    )
    
    # Формируем результат
    result = [
        finals,
        first_finals,
        values
    ]
    
    return result