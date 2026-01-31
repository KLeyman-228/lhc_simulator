import sys
import os
import pdg
import shutil
import random
from math import exp, sqrt
import numpy as np
from collections import defaultdict
from particle import Particle
from functools import lru_cache

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ PDG API
# ============================================================================

# путь к проекту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# pdg.sqlite лежит рядом с этим файлом
os.environ["PDG_DATA"] = BASE_DIR

# создаётся ОДИН РАЗ на worker
api = pdg.connect()

# Глобальный кэш для частиц
_particle_cache = {}



# ============================================================================
# КОНСТАНТЫ
# ============================================================================

TEMPERATURE_SCALE = 0.16
GAMMA_S = 0.3
GAMMA_C = 0.01
GAMMA_B = 0.001

MIN_MASS = 0.01
MAX_MASS_FRACTION = 0.7

# ============================================================================
# УТИЛИТЫ (с кэшированием)
# ============================================================================

@lru_cache(maxsize=1000)
def safe_mass(p):
    try:
        return p.mass if p.mass is not None else 0.0
    except:
        return 0.0

@lru_cache(maxsize=1000)
def safe_charge(p):
    try:
        #p = api.get_particle_by_mcid(mcid)
        return p.charge
    except:
        return 0


@lru_cache(maxsize=1000)
def get_particle_quarks(mcid):
    """Кэшированное получение кварков частицы"""
    try:
        item = Particle.from_pdgid(mcid)
        return item.quarks
    except:
        return ""


@lru_cache(maxsize=1000)
def is_resonance(name):
    """Проверка является ли частица резонансом"""
    if '(' in name and ')' in name:
        return True
    if '~' in name:
        return True
    
    resonance_markers = ['Delta', 'N(', 'Sigma(', 'Lambda(', 'Xi(']
    return any(marker in name for marker in resonance_markers)


@lru_cache(maxsize=1000)
def get_baryon_number(mcid):
    """Вычисление барионного числа с кэшированием"""
    try:
        quarks = get_particle_quarks(mcid)
        count = sum(-1 if q.isupper() else 1 for q in quarks)
        return count / 3
    except:
        return 0


@lru_cache(maxsize=1000)
def get_quark_number(mcid, quark):
    """Вычисление квантового числа для кварка с кэшированием"""
    try:
        quarks = get_particle_quarks(mcid)
        count = 0
        
        for q in quarks:
            if q.lower() == quark:
                if q.islower():  # кварк
                    count += -1 if quark == 's' else 1
                else:  # антикварк
                    count += 1 if quark == 's' else -1
        
        return count
    except:
        return 0


# ============================================================================
# ЗАГРУЗКА ЧАСТИЦ (ОПТИМИЗИРОВАННАЯ)
# ============================================================================

def load_particles():
    """Быстрая загрузка частиц из базы данных"""
    print("% Загрузка частиц из базы...")
    particles = []
    resonances = []
    
    # Получаем все частицы одним запросом
    all_pdgids = list(api.get_particles())
    
    #print(f"   Обработка {len(all_pdgids)} записей...")
    
    for i, pdg_entry in enumerate(all_pdgids):
        #if i % 100 == 0:
            #print(f"   Прогресс: {i}/{len(all_pdgids)}", end='\r')
        
        try:
            for particle in api.get(pdg_entry.pdgid):
                if not (particle.is_baryon or particle.is_meson):
                    continue
                if particle.mcid is None:
                    continue

                # Кэшируем частицу
                _particle_cache[particle.mcid] = particle
                
                # Разделяем на частицы и резонансы
                if is_resonance(particle.name) or (particle.width and particle.width > 0):
                    resonances.append(particle)
                else:
                    particles.append(particle)
        except:
            continue
    
    print(f"\n$ Загружено {len(particles)} частиц, {len(resonances)} резонансов")
    return particles, resonances


# ============================================================================
# ВЫЧИСЛЕНИЕ ВЕСОВ (ОПТИМИЗИРОВАНО)
# ============================================================================

def calculate_temperature(sqrt_s):
    """Быстрое вычисление температуры"""
    T_base = TEMPERATURE_SCALE
    
    if sqrt_s < 5.0:
        return T_base * 0.8
    elif sqrt_s < 20.0:
        return T_base * (0.8 + 0.1 * (sqrt_s - 5.0) / 15.0)
    else:
        return T_base * 1.2

def generate_weight(particle, sqrt_s):
    """
    Упрощенное и быстрое вычисление веса
    """
    m = safe_mass(particle)
    
    # Быстрые фильтры
    if m > sqrt_s * MAX_MASS_FRACTION:
        return 0.0
    
    if sqrt_s < 10.0 and m > 2.0:
        return 0.0
    if sqrt_s < 5.0 and m > 1.5:
        return 0.0
    if sqrt_s < 2.0 and m > 1.0:
        return 0.0
    
    try:
        T = 0.16
        gamma_s = 0.3
        gamma_c = 0.001
        
        J = particle.quantum_J
        quarks = get_particle_quarks(particle.mcid)
        
        n_s = quarks.count('s') + quarks.count('S')
        n_c = quarks.count('c') + quarks.count('C')
        
        weight = (2 * J + 1) * exp(-m / T) * (gamma_s ** n_s) * (gamma_c ** n_c)
        
        # Усиление для протонов и нейтронов
        if particle.mcid in [2212, 2112]:
            weight *= 5
        
        return weight if weight >= 1e-12 else 0.0
        
    except:
        return 0.0

def get_weights(particles_list, sqrt_s):
    """
    Быстрое вычисление весов для списка частиц
    """
    valid_particles = []
    weights = []
    
    # Быстрая фильтрация и вычисление весов
    for particle in particles_list:
        w = generate_weight(particle, sqrt_s)
        if w > 0:
            valid_particles.append(particle)
            weights.append(w)
    
    if not valid_particles:
        raise ValueError("Нет доступных частиц для данной энергии")
    
    # Преобразование в numpy для быстрых операций
    weights = np.array(weights, dtype=np.float64)
    
    # Добавляем шум
    noise = np.random.normal(1.0, 0.1, len(weights))
    weights *= np.clip(noise, 0.5, 2.0)
    
    # Нормализация
    probabilities = weights / np.sum(weights)
    
    return probabilities, valid_particles


# ============================================================================
# ПРОВЕРКА ЗАКОНОВ СОХРАНЕНИЯ (ОПТИМИЗИРОВАНО)
# ============================================================================

def check_conservation(particles, initial_state, sqrt_s):
    """
    Быстрая проверка законов сохранения
    """
    # Создание массивов нужных свойств
    masses = np.array([safe_mass(p) for p in particles])
    charges = np.array([safe_charge(p) for p in particles])
    baryons = np.array([get_baryon_number(p.mcid) for p in particles])
    strangenesses = np.array([get_quark_number(p.mcid, 's') for p in particles])
    charms = np.array([get_quark_number(p.mcid, 'c') for p in particles])
    bottoms = np.array([get_quark_number(p.mcid, 'b') for p in particles])

    # Выполняем суммирование
    total_mass = np.sum(masses)
    final_state = {
        'charge': np.sum(charges),
        'baryon': np.sum(baryons),
        'strangeness': np.sum(strangenesses),
        'charm': np.sum(charms),
        'bottom': np.sum(bottoms)
    }
    
    # Кинематика
    if total_mass > sqrt_s * 1.1:
        return False
    
    # Квантовые числа
    tolerance = 1e-9
    for key in initial_state:
        if abs(final_state[key] - initial_state[key]) > tolerance:
            return False
    
    return True

"""    total_mass = 0.0
    final_state = defaultdict(float)
    total_mass = np.sum([safe_mass(p.mcid) for p in particles])
    
    for particle in particles:
        mcid = particle.mcid
        total_mass += safe_mass(particle)
        final_state['charge'] += safe_charge(particle)
        final_state['baryon'] += get_baryon_number(mcid)
        final_state['strangeness'] += get_quark_number(mcid, 's')
        final_state['charm'] += get_quark_number(mcid, 'c')
        final_state['bottom'] += get_quark_number(mcid, 'b')
    import numpy as np"""

def is_valid_final_state(particles):
    """Проверка что все частицы - барионы или мезоны"""
    return all(p.is_baryon or p.is_meson for p in particles)



def generate_event(id1, id2, beam_energy, particles_list, resonances, max_attempts=100000):
    
    # ИСПРАВЛЕНИЕ: проверка входных данных
    if not particles_list or not resonances:
        print("❌ ОШИБКА: Пустые списки частиц или резонансов")
        return None
    
    A = api.get_particle_by_mcid(id1)
    B = api.get_particle_by_mcid(id2)
    # Вычисляем энергию центра масс
    m1 = safe_mass(A)
    m2 = safe_mass(B)
    s = m1**2 + m2**2 + 2 * m2 * beam_energy
    sqrt_s = sqrt(max(0.1, s))
    
    # Квантовые числа начального состояния
    initial_state = {
        'charge': safe_charge(A) + safe_charge(B),
        'baryon': get_baryon_number(id1) + get_baryon_number(id2),
        'strangeness': get_quark_number(id1, 's') + get_quark_number(id2, 's'),
        'charm': get_quark_number(id1, 'c') + get_quark_number(id2, 'c'),
        'bottom': get_quark_number(id1, 'b') + get_quark_number(id2, 'b')
    }
    
    # ОПТИМИЗАЦИЯ: предфильтруем резонансы по массе
    valid_resonances = [r for r in resonances if safe_mass(r) < sqrt_s * 0.8]
    
    if not valid_resonances:
        print(f"⚠️  Нет подходящих резонансов для энергии {sqrt_s:.2f} ГэВ")
        return None
    
    print(f"🔄 Генерация события: √s = {sqrt_s:.2f} ГэВ")
    print(f"   Доступно {len(particles_list)} частиц, {len(valid_resonances)} резонансов")
    
    successful_attempts = 0
    
    for attempt in range(max_attempts):
        #if attempt % 10000 == 0 and attempt > 0:
            #print(f"   Попытка {attempt}/{max_attempts} (успешных проверок: {successful_attempts})", end='\r')
        
        try:
            # Выбираем случайные частицу и резонанс
            chosen_particle = random.choice(particles_list)
            chosen_resonance = random.choice(valid_resonances)
            
            # ИСПРАВЛЕНИЕ: проверяем что резонанс может распадаться
            
            try:
                branching_fractions = api.get_particle_by_name(chosen_resonance.name).exclusive_branching_fractions()
                if not branching_fractions:
                    continue
            except Exception as e:
                continue
            
            # Перебираем каналы распада
            for branching in branching_fractions:
                try:
                    decay_products = [p.item.particle for p in branching.decay_products]
                    
                    # Добавляем выбранную частицу
                    final_products = decay_products + [chosen_particle]
                    
                    # Проверяем законы сохранения
                    if check_conservation(final_products, initial_state, sqrt_s) and is_valid_final_state(final_products):
                        
                        successful_attempts += 1
                        
                        # Формируем результат
                        products = {f'id_{i+1}': p.mcid for i, p in enumerate(final_products)}
                        
                        first_products = [{
                            "id_1": chosen_particle.mcid,
                            "id_2": chosen_resonance.mcid
                        }]
                        
                        values = [{
                            "Mass": sqrt_s,
                            "BaryonNum": initial_state['baryon'],
                            "S,B,C": [
                                initial_state['strangeness'],
                                initial_state['bottom'],
                                initial_state['charm']
                            ],
                            "Charge": initial_state['charge']
                        }]
                        
                        print(f"\n✓ Событие найдено после {attempt + 1} попыток")
                        return [products], first_products, values
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(e)
            continue
    
    print(f"\n❌ Событие не найдено после {max_attempts} попыток")
    print(f"   Успешных проверок законов сохранения: {successful_attempts}")
    return None




def SimulationEvent(id_1, id_2, beam_energy, particle_list, resonances):
    """
    Симуляция одного события столкновения
    
    Args:
        id_1: Monte Carlo ID первой частицы
        id_2: Monte Carlo ID второй частицы
        beam_energy: Энергия пучка (ГэВ)
        particle_list: Список частиц
        resonances: Список резонансов
    
    Returns:
        (event, first_products, values) или None
    """
    
    # ИСПРАВЛЕНИЕ: проверка входных данных
    if not particle_list:
        print("❌ ОШИБКА: Список частиц пуст! Сначала вызовите load_particles()")
        return None
    
    if not resonances:
        print("❌ ОШИБКА: Список резонансов пуст! Сначала вызовите load_particles()")
        return None
    
    print(f"\n{'='*60}")
    print(f"🎯 СИМУЛЯЦИЯ СТОЛКНОВЕНИЯ")
    print(f"   Частица 1: {id_1}")
    print(f"   Частица 2: {id_2}")
    print(f"   Энергия пучка: {beam_energy} ГэВ")
    print(f"{'='*60}")
    
    result = generate_event(id_1, id_2, beam_energy, particle_list, resonances)
    
    if result:
        event, first_products, values = result
        print(f"\n✓ УСПЕХ! Событие сгенерировано")
        print(f"   Продукты реакции: {event}")
        print(f"   Первичные частицы: {first_products}")
        print(f"   Параметры: {values}")
        return event, first_products, values
    else:
        print(f"\n✗ НЕУДАЧА: Событие не сгенерировано")
        print(f"   Попробуйте:")
        print(f"   - Увеличить энергию пучка")
        print(f"   - Использовать другие начальные частицы")
        print(f"   - Проверить что списки частиц загружены корректно")
        return None

