import os
import pdg
import random
from math import exp, sqrt
import numpy as np
from collections import defaultdict
from particle import Particle
from functools import lru_cache

# ============================================================================ 
# ИНИЦИАЛИЗАЦИЯ PDG API
# ============================================================================ 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["PDG_DATA"] = BASE_DIR
api = pdg.connect()

# Глобальный кэш для частиц и предрасчёт квантовых чисел
_particle_cache = {}
PARTICLE_QNUM = {}
RESONANCE_DECAYS = {}

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
        return p.charge
    except:
        return 0

@lru_cache(maxsize=1000)
def get_particle_quarks(mcid):
    try:
        item = Particle.from_pdgid(mcid)
        return item.quarks
    except:
        return ""

@lru_cache(maxsize=1000)
def is_resonance(name):
    if '(' in name and ')' in name:
        return True
    if '~' in name:
        return True
    resonance_markers = ['Delta', 'N(', 'Sigma(', 'Lambda(', 'Xi(']
    return any(marker in name for marker in resonance_markers)

@lru_cache(maxsize=1000)
def get_baryon_number(mcid):
    try:
        quarks = get_particle_quarks(mcid)
        count = sum(-1 if q.isupper() else 1 for q in quarks)
        return count / 3
    except:
        return 0

@lru_cache(maxsize=1000)
def get_quark_number(mcid, quark):
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
    print("% Загрузка частиц из базы...")
    particles = []
    resonances = []

    all_pdgids = list(api.get_particles())

    for i, pdg_entry in enumerate(all_pdgids):
        try:
            for particle in api.get(pdg_entry.pdgid):
                if not (particle.is_baryon or particle.is_meson):
                    continue
                if particle.mcid is None:
                    continue

                # Кэшируем частицу
                _particle_cache[particle.mcid] = particle

                # Предрасчёт квантовых чисел
                PARTICLE_QNUM[particle.mcid] = {
                    "mass": safe_mass(particle),
                    "charge": safe_charge(particle),
                    "baryon": get_baryon_number(particle.mcid),
                    "s": get_quark_number(particle.mcid, "s"),
                    "c": get_quark_number(particle.mcid, "c"),
                    "b": get_quark_number(particle.mcid, "b"),
                    "J": particle.quantum_J
                }

                # Предвыборка резонансов
                if is_resonance(particle.name) or (particle.width and particle.width > 0):
                    resonances.append(particle)
                    try:
                        bf = api.get_particle_by_name(particle.name).exclusive_branching_fractions()
                        if bf:
                            RESONANCE_DECAYS[particle.mcid] = bf
                    except:
                        continue
                else:
                    particles.append(particle)
        except:
            continue

    print(f"\n$ Загружено {len(particles)} частиц, {len(resonances)} резонансов")
    return particles, resonances

# ============================================================================ 
# ВЫЧИСЛЕНИЕ ВЕСОВ
# ============================================================================ 

def calculate_temperature(sqrt_s):
    T_base = TEMPERATURE_SCALE
    if sqrt_s < 5.0:
        return T_base * 0.8
    elif sqrt_s < 20.0:
        return T_base * (0.8 + 0.1 * (sqrt_s - 5.0) / 15.0)
    else:
        return T_base * 1.2

def generate_weight(particle, sqrt_s):
    m = PARTICLE_QNUM[particle.mcid]["mass"]

    if m > sqrt_s * MAX_MASS_FRACTION:
        return 0.0
    if sqrt_s < 10.0 and m > 2.0:
        return 0.0
    if sqrt_s < 5.0 and m > 1.5:
        return 0.0
    if sqrt_s < 2.0 and m > 1.0:
        return 0.0

    try:
        T = TEMPERATURE_SCALE
        gamma_s = GAMMA_S
        gamma_c = GAMMA_C
        J = PARTICLE_QNUM[particle.mcid]["J"]
        n_s = PARTICLE_QNUM[particle.mcid]["s"]
        n_c = PARTICLE_QNUM[particle.mcid]["c"]

        weight = (2 * J + 1) * exp(-m / T) * (gamma_s ** n_s) * (gamma_c ** n_c)

        if particle.mcid in [2212, 2112]:
            weight *= 5

        return weight if weight >= 1e-12 else 0.0
    except:
        return 0.0

def get_weights(particles_list, sqrt_s):
    valid_particles = []
    weights = []

    for particle in particles_list:
        w = generate_weight(particle, sqrt_s)
        if w > 0:
            valid_particles.append(particle)
            weights.append(w)

    if not valid_particles:
        raise ValueError("Нет доступных частиц для данной энергии")

    weights = np.array(weights, dtype=np.float64)
    noise = np.random.normal(1.0, 0.1, len(weights))
    weights *= np.clip(noise, 0.5, 2.0)
    probabilities = weights / np.sum(weights)

    return probabilities, valid_particles

# ============================================================================ 
# ПРОВЕРКА ЗАКОНОВ СОХРАНЕНИЯ
# ============================================================================ 

def check_conservation(particles, initial_state, sqrt_s):
    masses = np.array([PARTICLE_QNUM[p.mcid]["mass"] for p in particles])
    charges = np.array([PARTICLE_QNUM[p.mcid]["charge"] for p in particles])
    baryons = np.array([PARTICLE_QNUM[p.mcid]["baryon"] for p in particles])
    strangenesses = np.array([PARTICLE_QNUM[p.mcid]["s"] for p in particles])
    charms = np.array([PARTICLE_QNUM[p.mcid]["c"] for p in particles])
    bottoms = np.array([PARTICLE_QNUM[p.mcid]["b"] for p in particles])

    total_mass = np.sum(masses)
    final_state = {
        'charge': np.sum(charges),
        'baryon': np.sum(baryons),
        'strangeness': np.sum(strangenesses),
        'charm': np.sum(charms),
        'bottom': np.sum(bottoms)
    }

    if total_mass > sqrt_s * 1.1:
        return False

    tolerance = 1e-9
    for key in initial_state:
        if abs(final_state[key] - initial_state[key]) > tolerance:
            return False

    return True

def is_valid_final_state(particles):
    return all(p.is_baryon or p.is_meson for p in particles)

# ============================================================================ 
# ГЕНЕРАЦИЯ СОБЫТИЯ
# ============================================================================ 

def generate_event(id1, id2, beam_energy, particles_list, resonances, max_attempts=100000):
    if not particles_list or not resonances:
        print("❌ ОШИБКА: Пустые списки частиц или резонансов")
        return None

    A = api.get_particle_by_mcid(id1)
    B = api.get_particle_by_mcid(id2)
    m1 = PARTICLE_QNUM[id1]["mass"]
    m2 = PARTICLE_QNUM[id2]["mass"]
    s = m1**2 + m2**2 + 2 * m2 * beam_energy
    sqrt_s = sqrt(max(0.1, s))

    initial_state = {
        'charge': PARTICLE_QNUM[id1]["charge"] + PARTICLE_QNUM[id2]["charge"],
        'baryon': PARTICLE_QNUM[id1]["baryon"] + PARTICLE_QNUM[id2]["baryon"],
        'strangeness': PARTICLE_QNUM[id1]["s"] + PARTICLE_QNUM[id2]["s"],
        'charm': PARTICLE_QNUM[id1]["c"] + PARTICLE_QNUM[id2]["c"],
        'bottom': PARTICLE_QNUM[id1]["b"] + PARTICLE_QNUM[id2]["b"]
    }

    valid_resonances = [r for r in resonances if PARTICLE_QNUM[r.mcid]["mass"] < sqrt_s * 0.8]
    if not valid_resonances:
        print(f"⚠️  Нет подходящих резонансов для энергии {sqrt_s:.2f} ГэВ")
        return None

    print(f"🔄 Генерация события: √s = {sqrt_s:.2f} ГэВ")
    print(f"   Доступно {len(particles_list)} частиц, {len(valid_resonances)} резонансов")

    successful_attempts = 0

    for attempt in range(max_attempts):
        try:
            chosen_particle = random.choice(particles_list)
            chosen_resonance = random.choice(valid_resonances)

            branching_fractions = RESONANCE_DECAYS.get(chosen_resonance.mcid)
            if not branching_fractions:
                continue

            for branching in branching_fractions:
                try:
                    decay_products = [p.item.particle for p in branching.decay_products]
                    final_products = decay_products + [chosen_particle]

                    if check_conservation(final_products, initial_state, sqrt_s) and is_valid_final_state(final_products):
                        successful_attempts += 1
                        products = {f'id_{i+1}': p.mcid for i, p in enumerate(final_products)}
                        first_products = [{"id_1": chosen_particle.mcid, "id_2": chosen_resonance.mcid}]
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
                except:
                    continue
        except:
            continue

    print(f"\n❌ Событие не найдено после {max_attempts} попыток")
    print(f"   Успешных проверок законов сохранения: {successful_attempts}")
    return None

# ============================================================================ 
# ВЫЗОВ СИМУЛЯЦИИ
# ============================================================================ 

def SimulationEvent(id_1, id_2, beam_energy, particle_list, resonances):
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
        return None
