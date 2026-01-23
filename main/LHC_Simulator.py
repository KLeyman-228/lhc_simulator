import sys
import os
import pdg
import shutil
import numpy, random
from math import *
import time
import numpy as np
from collections import Counter
from particle import Particle
# FOR CONSOLE:
from progress.bar import IncrementalBar

# Если запущено из exe

if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
    pdg_db_temp = os.path.join(base_path, "pdg", "pdg.sqlite")
    exe_dir = os.path.dirname(sys.executable)
    pdg_db_work = os.path.join(exe_dir, "pdg.sqlite")
    particle_data_path = os.path.join(base_path, "particle", "data")
    if not os.path.exists(pdg_db_work):
        shutil.copy(pdg_db_temp, pdg_db_work)
    db_url = f"sqlite:///{pdg_db_work}"
else:
    pdg_db_work = os.path.join("pdg", "pdg.sqlite")
    db_url = f"sqlite:///{pdg_db_work}"
    particle_data_path = os.path.join("particle", "data")

# PDG API INIT
#api = pdg.connect(db_url)
api = pdg.connect()



# FUNCTIONS:

def load_particles():
    print("Загрузка частиц из базы...")
    particles, resonance = [], []
    
    for i in api.get_particles():
        for particle in api.get(i.pdgid):
            if (particle.is_baryon or particle.is_meson):
                (resonance if particle.width and particle.width > 0 
                 else particles).append(particle) \
                    if not is_resonance(particle) and not is_antiparticle(particle) else None
    
    print(f"Загружено {len(particles)} частиц")
    return particles, resonance


def safe_mass(m):
    try:
        if m.mass is not None:
            return m.mass
        else:
            return 0
    except:
        return 0
    
def safe_charge(m):
    try:
        return m.charge
    except:
        return 0

def is_antiquark(q):
    return q.isupper()

def is_antiparticle(p):
    return 'bar' in p.name

def is_resonance(p):
    name = p.name

    # возбужденные состояния по имени
    if '(' in name and ')' in name:
        return True

    # тильда — мусорные состояния
    if '~' in name:
        return True

    # Delta, N*, Sigma*, Xi*, Lambda*
    if any(x in name for x in ['Delta', 'N(', 'Sigma(', 'Lambda(', 'Xi(']):
        return True

    return False

def get_B(p):
    try:
        quarks = 0
        item = Particle.from_pdgid(p.mcid)
        for q in item.quarks:
            if q.isupper():
                quarks -= 1
            else:
                quarks += 1
        res_b = quarks / 3
        return res_b
    except:
        return 0

def get_quantWord(p, quark):
    """Вычисление квантового числа для кварка"""
    try:
        item = Particle.from_pdgid(p.mcid)
        quarks = getattr(item, "quarks", "")
        count = 0
        for q in quarks:
            if q.lower() == quark:
                if q.islower():  # кварк
                    count -= 1 if quark == 's' else 1
                else:  # антикварк
                    count += 1 if quark == 's' else -1
        return count
    except:
        return 0


def get_quark_number(particle, quark):
    """Вычисление квантового числа для кварка"""
    try:
        item = Particle.from_pdgid(particle.mcid)
        quarks = getattr(item, "quarks", "")
        count = 0
        for q in quarks:
            if q.lower() == quark:
                if q.islower():  # кварк
                    count -= 1 if quark == 's' else 1
                else:  # антикварк
                    count += 1 if quark == 's' else -1
        return count
    except:
        return 0
    
# КОНСТАНТЫ С ПРАВИЛЬНЫМИ ФИЗИЧЕСКИМИ ПАРАМЕТРАМИ
TEMPERATURE_SCALE = 0.16  # Температура для статистической модели
GAMMA_S = 0.3    # Подавление странных кварков
GAMMA_C = 0.01   # Подавление очарованных кварков (увеличил с 0.001)
GAMMA_B = 0.001  # Подавление прелестных кварков (увеличил с 0.05)



# ФИЗИЧЕСКИЕ ОГРАНИЧЕНИЯ
MIN_MASS = 0.01    # Минимальная масса частицы
MAX_MASS_FRACTION = 0.7  # Максимальная доля √s, уходящая в массу

def calculate_particle_weight(particle, sqrt_s):
    """
    Вычисление веса для ОДНОЙ частицы
    Возвращает вес (не вероятность!) или 0.0 если частица не может родиться при данной энергии
    """
    # Получаем свойства частицы

    m = safe_mass(particle)
    
    # ЖЁСТКИЙ ФИЛЬТР ПО МАССЕ
    if m > sqrt_s * MAX_MASS_FRACTION:  # Не более 70% энергии в массу
        return 0.0
    
    # Для низких энергий запрещаем тяжёлые частицы
    if sqrt_s < 10.0 and m > 2.0:
        return 0.0
    
    if sqrt_s < 5.0 and m > 1.5:
        return 0.0
    
    if sqrt_s < 2.0 and m > 1.0:
        return 0.0
    
    try:
        item = Particle.from_pdgid(particle.mcid)
        # Температура зависит от энергии
        T_base = TEMPERATURE_SCALE
        if sqrt_s < 5.0:
            T = T_base * 0.8  # Низкие энергии - ниже температура
        elif sqrt_s < 20.0:
            T = T_base * (0.8 + 0.1 * (sqrt_s - 5.0) / 15.0)
        else:
            T = T_base * 1.2  # Высокие энергии - выше температура
        
        # 1. МАССОВЫЙ ФАКТОР (самый важный!)
        # Экспоненциальное подавление тяжёлых частиц
        mass_factor = exp(-m / T)
        
        # Дополнительное подавление для очень тяжёлых частиц
        if m > 2.0:
            mass_factor *= 0.1
        elif m > 1.0:
            mass_factor *= 0.5
        
        # 2. СПИНОВЫЙ ФАКТОР
        J = particle.quantum_J
        spin_factor = (2 * J + 1) ** 0.5  # Ослабляем влияние спина
        
        # 3. КВАРКОВЫЕ ПОДАВЛЕНИЯ
        quarks = item.quarks
        
        # Подсчёт кварков
        quark_counts = {
            's': quarks.count("s") + quarks.count("S"),
            'c': quarks.count("c") + quarks.count("C"),
            'b': quarks.count("b") + quarks.count("B")
        }
        
        # Странные кварки
        strange_factor = GAMMA_S ** (quark_counts['s'] * 0.8)
        
        # Очарованные кварки (сильное подавление)
        charm_factor = GAMMA_C ** (quark_counts['c'] * 1.5)  # Усиленное подавление
        
        # Прелестные кварки (очень сильное подавление)
        bottom_factor = GAMMA_B ** (quark_counts['b'] * 2.0)  # Очень сильное подавление
        
        quark_factor = strange_factor * charm_factor * bottom_factor
        
        # 4. СТАБИЛЬНОСТЬ
        
        # 5. ТИП ЧАСТИЦЫ
        type_factor = 1.0
        if particle.is_baryon:
            type_factor = 1.5  # Барионы немного усилены
        elif particle.is_meson and m < 0.5:
            type_factor = 1.2  # Лёгкие мезоны
        
        # 6. "ОБЫЧНОСТЬ" ЧАСТИЦЫ
        # Определяем является ли частица "обычной"
        S = get_quantWord(particle, 's')
        C = get_quantWord(particle, 'c')
        Bt = get_quantWord(particle, 'b')
        width = particle.width
        
        is_common = (
            m < 2.0 and
            abs(S) <= 2 and
            abs(C) <= 1 and
            Bt == 0 and
            width < 0.2
        )
        
        common_factor = 5.0 if is_common else 1.0
        
        # 7. РЕЗОНАНСЫ
        resonance_factor = 1.0
        if width > 0:
            # Для резонансов используем Брейт-Вигнер
            if sqrt_s > m:  # Только если энергия выше массы
                bw = width**2 / 4.0
                denom = (sqrt_s - m)**2 + bw
                if denom > 0:
                    resonance_factor = bw / denom * 10
                    resonance_factor = min(resonance_factor, 2.0)
            else:
                resonance_factor = 0.1  # Сильное подавление ниже порога
        
        # 8. ЭНЕРГЕТИЧЕСКАЯ ЗАВИСИМОСТЬ
        energy_factor = 1.0
        if sqrt_s < 10.0:
            # При низких энергиях усиливаем лёгкие частицы
            if m < 0.5:
                energy_factor = 2.0
            elif m < 1.0:
                energy_factor = 1.5
        
        # ИТОГОВЫЙ ВЕС
        weight = (
            mass_factor * 
            spin_factor * 
            quark_factor * 
            type_factor * 
            common_factor * 
            resonance_factor * 
            energy_factor
        )
        
        # МИНИМАЛЬНЫЙ ВЕС
        if weight < 1e-12:
            return 0.0
        
        return weight
        
    except Exception as e:
        return 0.0

def generate_weight(p, s):
    try:
        T = 0.16
        gamma_s = 0.3
        gamma_c = 0.001

        item = Particle.from_pdgid(p.mcid)
        
        m = safe_mass(p)
        J = eval(p.quantum_J)
        
        quarks = item.quarks
        n_s = quarks.count('s')
        n_c = quarks.count('c')

        weight = (2*J+1)*exp(-m/T)*(gamma_s**n_s)*(gamma_c**n_c)
        
        if p.mcid in [2212, 2112]:
            weight *= 20
        return weight
    except:
        return 0
    
def get_weigths(particles_list, sqrt_s):

    valid_particles = []
    valid_resonances = []
    weights = []
    weights_r = []

    for particle in particles_list:
        w = generate_weight(particle, sqrt_s)
        if w > 0:# and safe_mass(particle) < 0.6 * sqrt_s:
            valid_particles.append(particle)
            weights.append(w)

    if not valid_particles:
        print('LOX')

    # Нормализуем веса с температурой для сглаживания
    weights = np.array(weights)

    # Добавляем небольшой шум для разнообразия
    noise = np.random.normal(1.0, 0.1, len(weights))
    weights = weights * np.clip(noise, 0.5, 2.0)

    # Нормализация
    total_weight = np.sum(weights)
    probabilities = weights / total_weight

    return probabilities, valid_particles

def check_conservation(particles, initial_state, sqrt_s):

    total_mass = 0.0
    final_state = {
        'charge': 0,
        'baryon': 0,
        'strangeness': 0,
        'charm': 0,
        'bottom': 0
    }

    for particle in particles:
        total_mass += safe_mass(particle)
        final_state['charge'] += safe_charge(particle)
        final_state['baryon'] += get_B(particle)
        final_state['strangeness'] += get_quantWord(particle, 's')
        final_state['charm'] += get_quantWord(particle, 'c')
        final_state['bottom'] += get_quantWord(particle, 'b')

    # кинематика
    if total_mass > sqrt_s * 1.1:
        return False

    # квантовые числа
    for key in initial_state:
        if final_state[key] != initial_state[key]:
            return False

    return True

def is_ppp(ps):
    for p in ps:
        if p.is_baryon or p.is_meson:
            return True
        return False





def generate_event(id1, id2, beam_energy, particles_list, resonances, max_attempts=100000):
    """Генерация одного события столкновения"""
    # Получаем исходные частицы

    A = api.get_particle_by_mcid(id1)
    B = api.get_particle_by_mcid(id2)
    
    # Вычисляем энергию центра масс
    m1 = safe_mass(A)
    m2 = safe_mass(B)
    s = m1**2 + m2**2 + 2 * m2 * beam_energy
    sqrt_s = sqrt(max(0.1, s))
    
    # Квантовые числа начального состояния
    initial_state = {
        'charge': getattr(A, 'charge', 0) + getattr(B, 'charge', 0),
        'baryon': get_B(A) + get_B(B),
        'strangeness': get_quantWord(A, 's') + get_quantWord(B, 's'),
        'charm': get_quantWord(A, 'c') + get_quantWord(B, 'c'),
        'bottom': get_quantWord(A, 'b') + get_quantWord(B, 'b')
    }
    
    for attempt in range(max_attempts):
        Products = []
        # Выбираем количество частиц (2-6)
        #n_particles = np.random.choice([2, 3, 4, 5, 6], p=[0.2, 0.35, 0.2, 0.15, 0.1])
        n_particles = 2
        # Выбираем частицы с учётом весов
        #chosen_indices_p = np.random.choice(len(particles_list), size=1)
        #chosen_indices_r = np.random.choice(len(resonances), size=1)
        chosen_particles = random.choice(particles_list)
        chosen_resonances = random.choice(resonances)

        #Products = chosen_resonances + chosen_particles
        #print(chosen_particles, chosen_resonances)
        # Проверяем законы сохранения
        try:

            for particle in api.get_particle_by_name(chosen_resonances.name).exclusive_branching_fractions():  

                decay_products = [p.item.particle for p in particle.decay_products]
                decay_products.append(chosen_particles)

                FirstProducts = [{
                    "id_1": chosen_particles.mcid,
                    "id_2": chosen_resonances.mcid
                }]
                Products = decay_products

                values = [{

                        "Mass": sqrt_s,
                        "BaryonNum": initial_state['baryon'],
                        "S,B,C": [initial_state['strangeness'], initial_state['bottom'], initial_state['charm']],
                        "Charge": initial_state['charge']

                }]

                if check_conservation(Products, initial_state, sqrt_s) and is_ppp(Products):
                    product = {}
                    for i, p in enumerate(Products):
                        product[f'id_{i+1}'] = p.mcid

                    return [product], FirstProducts, values
                else:
                    continue

        except Exception as e:
            #print(e)
            continue
    return None





resonances = []
particle_list = []

def SimulationEvent(id_1, id_2, E, particle_list, resonances):

    event, events, valies = generate_event(id_1, id_2, E, particle_list, resonances)

    if event:

        print(event, events, valies)
        return event, events, valies
    
    else:
        print('ERROR')
    


