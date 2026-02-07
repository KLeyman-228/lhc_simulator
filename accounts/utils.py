# accounts/utils.py
from django.db.models import F
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import SimulationLog

User = get_user_model()

# Очки за разные типы симуляций
SIMULATION_POINTS = {
    'hadron-hadron': 10,
    'lepton-lepton': 15,
    'hadron-boson': 20,
    'hadron-lepton': 25,
    'boson-boson': 30,
}


def add_simulation_rating(user, simulation_type, particles_detected=0, 
                         energy=None, duration=None, collision_results=None):
    """
    Добавить рейтинг пользователю за запуск симуляции
    
    Args:
        user: объект User или user.id (int)
        simulation_type: str - тип симуляции ('proton_proton', 'quark_collision' и т.д.)
        particles_detected: int - количество обнаруженных частиц
        energy: float - энергия в ТэВ (опционально)
        duration: int - длительность в секундах (опционально)
        collision_results: list - список строк с результатами (опционально)
    
    Returns:
        dict: информация об обновлении {
            'success': bool,
            'points_earned': int,
            'total_rating': int,
            'total_simulations': int,
            'simulation_id': int
        }
    """
    # Если передали ID, получаем объект User
    if isinstance(user, int):
        try:
            user = User.objects.get(id=user)
        except User.DoesNotExist:
            return {
                'success': False,
                'error': 'Пользователь не найден'
            }
    
    # Расчет очков
    base_points = SIMULATION_POINTS.get(simulation_type, 10)
    particle_bonus = min(particles_detected, 10)  # Макс +10 за частицы
    energy_bonus = 5 if energy and energy > 10 else 0  # +5 если энергия > 10 ТэВ
    
    total_points = base_points + particle_bonus + energy_bonus
    
    # Атомарное обновление счетчика (защита от race conditions)
    User.objects.filter(pk=user.pk).update(
        simulation_count=F('simulation_count') + 1,
        rating_score=F('rating_score') + total_points,
        last_simulation_at=timezone.now()
    )
    
    # Сохраняем лог симуляции
    simulation_log = SimulationLog.objects.create(
        user=user,
        simulation_type=simulation_type,
        particles_detected=particles_detected,
        energy=energy,
        duration=duration,
        collision_results=collision_results or []
    )
    
    # Обновляем объект user чтобы получить свежие данные
    user.refresh_from_db()
    
    return {
        'success': True,
        'points_earned': total_points,
        'total_rating': user.rating_score,
        'total_simulations': user.simulation_count,
        'simulation_id': simulation_log.id
    }