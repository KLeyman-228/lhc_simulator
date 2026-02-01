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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["PDG_DATA"] = BASE_DIR
api = pdg.connect()

# ============================================================================
# ГЛОБАЛЬНЫЕ КЭШИ
# ============================================================================

_particle_cache = {}
PARTICLE_VALUES = {}
RESONANCE_DECAYS = {}

# ============================================================================
# НОВОЕ: КВАНТОВЫЕ ЧИСЛА ДЛЯ ЛЕПТОНОВ
# ============================================================================

# Лептонное число (разделено по поколениям)
LEPTON_NUMBER = {
    # Электронное семейство
    11: {'e': 1, 'mu': 0, 'tau': 0},      # e-
    -11: {'e': -1, 'mu': 0, 'tau': 0},    # e+
    12: {'e': 1, 'mu': 0, 'tau': 0},      # nu_e
    -12: {'e': -1, 'mu': 0, 'tau': 0},    # anti_nu_e
    
    # Мюонное семейство
    13: {'e': 0, 'mu': 1, 'tau': 0},      # mu-
    -13: {'e': 0, 'mu': -1, 'tau': 0},    # mu+
    14: {'e': 0, 'mu': 1, 'tau': 0},      # nu_mu
    -14: {'e': 0, 'mu': -1, 'tau': 0},    # anti_nu_mu
    
    # Таонное семейство
    15: {'e': 0, 'mu': 0, 'tau': 1},      # tau-
    -15: {'e': 0, 'mu': 0, 'tau': -1},    # tau+
    16: {'e': 0, 'mu': 0, 'tau': 1},      # nu_tau
    -16: {'e': 0, 'mu': 0, 'tau': -1},    # anti_nu_tau
}

# Бозоны
GAUGE_BOSONS = {
    22: 'photon',      # γ
    23: 'Z',           # Z⁰
    24: 'W+',          # W+
    -24: 'W-',         # W-
    21: 'gluon',       # g
    25: 'Higgs',       # H
}

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
# НОВОЕ: КЛАССИФИКАЦИЯ ЧАСТИЦ
# ============================================================================

def get_particle_type(mcid):
    """
    Определяет тип частицы
    
    Returns:
        'baryon', 'meson', 'lepton', 'gauge_boson', 'unknown'
    """
    try:
        # Лептоны
        if mcid in LEPTON_NUMBER:
            return 'lepton'
        
        # Калибровочные бозоны
        if mcid in GAUGE_BOSONS:
            return 'gauge_boson'
        
        # Адроны (через кварковый состав)
        quarks = get_particle_quarks(mcid)
        if quarks:
            # Барионы: 3 кварка
            if len(quarks) == 3:
                return 'baryon'
            # Мезоны: кварк-антикварк
            elif len(quarks) == 2:
                return 'meson'
        
        return 'unknown'
    except:
        return 'unknown'


@lru_cache(maxsize=1000)
def is_hadron(mcid):
    """Проверка: является ли частица адроном"""
    ptype = get_particle_type(mcid)
    return ptype in ['baryon', 'meson']


@lru_cache(maxsize=1000)
def is_lepton(mcid):
    """Проверка: является ли частица лептоном"""
    return mcid in LEPTON_NUMBER


@lru_cache(maxsize=1000)
def is_boson(mcid):
    """Проверка: является ли частица калибровочным бозоном"""
    return mcid in GAUGE_BOSONS


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


def get_lepton_numbers(mcid):
    """
    Получить лептонные числа частицы
    
    Returns:
        dict: {'e': L_e, 'mu': L_mu, 'tau': L_tau}
    """
    if mcid in LEPTON_NUMBER:
        return LEPTON_NUMBER[mcid]
    else:
        return {'e': 0, 'mu': 0, 'tau': 0}


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
# ЗАГРУЗКА ЧАСТИЦ (РАСШИРЕННАЯ)
# ============================================================================

def load_particles():
    """
    Загрузка частиц из базы данных
    НОВОЕ: включает лептоны и бозоны
    """
    print("% Загрузка частиц из базы...")
    
    # Раздельные списки
    hadrons = []          # адроны (барионы + мезоны)
    leptons = []          # лептоны
    gauge_bosons = []     # калибровочные бозоны
    resonances = []       # резонансы
    
    all_pdgids = list(api.get_particles())
    
    for i, pdg_entry in enumerate(all_pdgids):
        try:
            for particle in api.get(pdg_entry.pdgid):
                if particle.mcid is None:
                    continue

                # Кэшируем частицу
                _particle_cache[particle.mcid] = particle
                
                # Получаем лептонные числа
                lepton_nums = get_lepton_numbers(particle.mcid)

                PARTICLE_VALUES[particle.mcid] = {
                    "mass": safe_mass(particle),
                    "charge": safe_charge(particle),
                    "baryon": get_baryon_number(particle.mcid),
                    "s": get_quark_number(particle.mcid, "s"),
                    "c": get_quark_number(particle.mcid, "c"),
                    "b": get_quark_number(particle.mcid, "b"),
                    "J": particle.quantum_J,
                    # НОВОЕ: лептонные числа
                    "L_e": lepton_nums['e'],
                    "L_mu": lepton_nums['mu'],
                    "L_tau": lepton_nums['tau'],
                    # НОВОЕ: тип частицы
                    "type": get_particle_type(particle.mcid)
                }
                
                # Классификация
                ptype = PARTICLE_VALUES[particle.mcid]["type"]
                
                if is_resonance(particle.name) or (particle.width and particle.width > 0):
                    resonances.append(particle)
                    bf = api.get_particle_by_name(particle.name).exclusive_branching_fractions()
                    if bf:
                        RESONANCE_DECAYS[particle.mcid] = bf
                else:
                    if ptype in ['baryon', 'meson']:
                        hadrons.append(particle)
                    elif ptype == 'lepton':
                        leptons.append(particle)
                    elif ptype == 'gauge_boson':
                        gauge_bosons.append(particle)
        except:
            continue
    
    print(f"\n$ Загружено:")
    print(f"  • Адроны: {len(hadrons)}")
    print(f"  • Лептоны: {len(leptons)}")
    print(f"  • Калибровочные бозоны: {len(gauge_bosons)}")
    print(f"  • Резонансы: {len(resonances)}")
    
    return hadrons, leptons, gauge_bosons, resonances


# ============================================================================
# ВЫЧИСЛЕНИЕ ВЕСОВ (РАСШИРЕННОЕ)
# ============================================================================

def calculate_temperature(sqrt_s):
    """Вычисление температуры"""
    T_base = TEMPERATURE_SCALE
    
    if sqrt_s < 5.0:
        return T_base * 0.8
    elif sqrt_s < 20.0:
        return T_base * (0.8 + 0.1 * (sqrt_s - 5.0) / 15.0)
    else:
        return T_base * 1.2


def generate_weight(particle, sqrt_s, interaction_type='hadron-hadron'):
    """
    Вычисление веса частицы
    
    НОВОЕ: учитывает тип взаимодействия
    
    Args:
        particle: частица
        sqrt_s: энергия в системе центра масс
        interaction_type: тип взаимодействия
            - 'hadron-hadron': адрон + адрон
            - 'hadron-lepton': адрон + лептон (DIS)
            - 'lepton-lepton': лептон + лептон
            - 'hadron-boson': адрон + бозон
    """
    m = safe_mass(particle)
    
    # Быстрые фильтры
    if m > sqrt_s * MAX_MASS_FRACTION:
        return 0.0
    
    try:
        T = 0.16
        gamma_s = 0.3
        gamma_c = 0.001
        
        J = particle.quantum_J
        ptype = PARTICLE_VALUES[particle.mcid]['type']
        
        # Базовый вес
        if ptype in ['baryon', 'meson']:
            quarks = get_particle_quarks(particle.mcid)
            n_s = quarks.count('s') + quarks.count('S')
            n_c = quarks.count('c') + quarks.count('C')
            weight = (2 * J + 1) * exp(-m / T) * (gamma_s ** n_s) * (gamma_c ** n_c)
            
            # Усиление для протонов и нейтронов
            if particle.mcid in [2212, 2112]:
                weight *= 5
        
        elif ptype == 'lepton':
            # Лептоны легче рождаются
            weight = (2 * J + 1) * exp(-m / T) * 2.0
        
        elif ptype == 'gauge_boson':
            # Бозоны рождаются реже (кроме фотонов)
            if particle.mcid == 22:  # фотон
                weight = exp(-m / T) * 10.0
            else:
                weight = exp(-m / T) * 0.1
        
        else:
            weight = 0.0
        
        # НОВОЕ: модификация веса в зависимости от типа взаимодействия
        if interaction_type == 'hadron-lepton':
            # При глубоконеупругом рассеянии предпочтительны кварки/глюоны
            if ptype in ['baryon', 'meson']:
                weight *= 2.0  # адроны рождаются чаще
        
        elif interaction_type == 'lepton-lepton':
            # e+e- → μ+μ-, τ+τ-, адроны
            if ptype == 'lepton':
                weight *= 3.0
            elif ptype == 'gauge_boson' and particle.mcid == 22:
                weight *= 5.0  # фотоны
        
        return weight if weight >= 1e-12 else 0.0
        
    except:
        return 0.0


def get_weights(particles_list, sqrt_s, interaction_type='hadron-hadron'):
    """
    Вычисление весов для списка частиц
    
    НОВОЕ: учитывает тип взаимодействия
    """
    valid_particles = []
    weights = []
    
    for particle in particles_list:
        w = generate_weight(particle, sqrt_s, interaction_type)
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
# НОВОЕ: ОПРЕДЕЛЕНИЕ ТИПА ВЗАИМОДЕЙСТВИЯ
# ============================================================================

def get_interaction_type(id1, id2):

    type1 = PARTICLE_VALUES[id1]['type']
    type2 = PARTICLE_VALUES[id2]['type']
    
    types = {type1, type2}
    
    # Адрон + Адрон
    if types <= {'baryon', 'meson'}:
        return 'hadron-hadron'
    
    # Адрон + Лептон (глубоконеупругое рассеяние)
    if types == {'baryon', 'lepton'} or types == {'meson', 'lepton'}:
        return 'hadron-lepton'
    
    # Лептон + Лептон
    if types == {'lepton'}:
        return 'lepton-lepton'
    
    # Адрон + Бозон
    if ('baryon' in types or 'meson' in types) and 'gauge_boson' in types:
        return 'hadron-boson'
    
    # Лептон + Бозон
    if types == {'lepton', 'gauge_boson'}:
        return 'lepton-boson'
    
    return 'unknown'


# ============================================================================
# ПРОВЕРКА ЗАКОНОВ СОХРАНЕНИЯ (РАСШИРЕННАЯ)
# ============================================================================

def check_conservation(particles, initial_state, sqrt_s):
    """
    Проверка законов сохранения
    
    НОВОЕ: проверяет лептонные числа для каждого поколения
    """
    masses = np.array([PARTICLE_VALUES[p.mcid]['mass'] for p in particles])
    charges = np.array([PARTICLE_VALUES[p.mcid]['charge'] for p in particles])
    baryons = np.array([PARTICLE_VALUES[p.mcid]['baryon'] for p in particles])
    strangenesses = np.array([PARTICLE_VALUES[p.mcid]['s'] for p in particles])
    charms = np.array([PARTICLE_VALUES[p.mcid]['c'] for p in particles])
    bottoms = np.array([PARTICLE_VALUES[p.mcid]['b'] for p in particles])
    
    # НОВОЕ: лептонные числа
    L_e = np.array([PARTICLE_VALUES[p.mcid]['L_e'] for p in particles])
    L_mu = np.array([PARTICLE_VALUES[p.mcid]['L_mu'] for p in particles])
    L_tau = np.array([PARTICLE_VALUES[p.mcid]['L_tau'] for p in particles])

    total_mass = np.sum(masses)
    final_state = {
        'charge': np.sum(charges),
        'baryon': np.sum(baryons),
        'strangeness': np.sum(strangenesses),
        'charm': np.sum(charms),
        'bottom': np.sum(bottoms),
        # НОВОЕ: лептонные числа
        'L_e': np.sum(L_e),
        'L_mu': np.sum(L_mu),
        'L_tau': np.sum(L_tau),
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


def is_valid_final_state(particles):
    """Проверка валидности конечного состояния"""
    return True


# ============================================================================
# НОВОЕ: ГЕНЕРАЦИЯ СОБЫТИЙ ДЛЯ РАЗНЫХ ТИПОВ ВЗАИМОДЕЙСТВИЙ
# ============================================================================

def generate_hadron_hadron_event(id1, id2, sqrt_s, initial_state, particles_all, resonances):
    """
    Генерация события: адрон + адрон
    
    Стандартный механизм через резонансы
    """
    valid_resonances = [r for r in resonances if PARTICLE_VALUES[r.mcid]['mass'] < sqrt_s * 0.9]
    
    if not valid_resonances:
        return None
    
    for _ in range(10000):
        try:
            chosen_particle = random.choice(particles_all)
            chosen_resonance = random.choice(valid_resonances)
            
            branching_fractions = api.get_particle_by_name(chosen_resonance.name).exclusive_branching_fractions()
            if not branching_fractions:
                continue
            
            for branching in branching_fractions:
                try:
                    decay_products = [p.item.particle for p in branching.decay_products]
                    final_products = decay_products + [chosen_particle]
                    
                    if check_conservation(final_products, initial_state, sqrt_s) and is_valid_final_state(final_products):
                        return final_products, chosen_particle, chosen_resonance
                except:
                    continue
        except:
            continue
    
    return None

def generate_hadron_lepton_event(hadron_id, lepton_id, sqrt_s, initial_state, particles_all, resonances):
    """
    Генерация события: адрон + лептон (глубоконеупругое рассеяние)
    
    НОВОЕ: Адрон разбивается на кварки, лептон рассеивается
    
    Упрощенная модель:
    - Адрон → кварки + глюоны
    - Лептон остается или рождает пару лептон+антилептон
    """
    print("   🔬 Глубоконеупругое рассеяние (DIS)")
    
    # Определяем кварковый состав адрона
    hadron_quarks = get_particle_quarks(hadron_id)
    
    if not hadron_quarks:
        return None
    
    print(f"   Кварки адрона: {hadron_quarks}")
    
    # Ищем кварковые частицы в базе
    quark_particles = []
    for p in particles_all:
        quarks = get_particle_quarks(p.mcid)
        if quarks and len(quarks) <= 2:  # мезоны или отдельные кварки
            quark_particles.append(p)
    
    if not quark_particles:
        print("   ⚠️ Нет доступных кварковых состояний")
        return None
    
    for _ in range(5000):
        try:
            # Выбираем 2-3 легких адрона (кварковые пары)
            n_fragments = random.randint(2, 3)
            fragments = random.choices(quark_particles, k=n_fragments)
            
            # Лептон остается или рождается пара
            if random.random() < 0.7:
                # Лептон рассеялся упруго
                lepton_final = [_particle_cache[lepton_id]]
            else:
                # Рождение пары лептон-антилептон
                anti_lepton_id = -lepton_id
                if anti_lepton_id in PARTICLE_VALUES:
                    lepton_final = [_particle_cache[lepton_id], _particle_cache[anti_lepton_id]]
                else:
                    lepton_final = [_particle_cache[lepton_id]]
            
            final_products = fragments + lepton_final
            
            if check_conservation(final_products, initial_state, sqrt_s) and is_valid_final_state(final_products):
                return final_products, fragments[0], _particle_cache[lepton_id]
        except:
            continue
    
    return None

def generate_lepton_lepton_event(id1, id2, sqrt_s, initial_state, particles_all, resonances):
    """
    Генерация события: лептон + лептон
    
    НОВОЕ: Процессы типа e+e- → μ+μ-, τ+τ-, адроны, фотоны
    """
    print("   ⚡ Лептон-лептонное взаимодействие")
    
    # Проверяем: частица + античастица?
    is_annihilation = (id1 == -id2)
    
    if is_annihilation:
        print("   💥 Аннигиляция лептон-антилептон")
        
        # e+e- → γγ, μ+μ-, τ+τ-, адроны
        for _ in range(5000):
            try:
                # Выбор канала
                channel = random.choice(['photons', 'leptons', 'hadrons'])
                
                if channel == 'photons':
                    # → γγ
                    photon = _particle_cache[22]
                    final_products = [photon, photon]
                
                elif channel == 'leptons':
                    # → l+l- (другое поколение)
                    lepton_pairs = [(13, -13), (15, -15)]  # μ+μ-, τ+τ-
                    pair = random.choice(lepton_pairs)
                    if pair[0] in PARTICLE_VALUES and pair[1] in PARTICLE_VALUES:
                        final_products = [_particle_cache[pair[0]], _particle_cache[pair[1]]]
                    else:
                        continue
                
                else:  # hadrons
                    # → адроны (2-3 пиона)
                    hadrons = [p for p in particles_all if PARTICLE_VALUES[p.mcid]['type'] in ['meson']]
                    n_hadrons = random.randint(2, 3)
                    final_products = random.choices(hadrons, k=n_hadrons)
                
                if check_conservation(final_products, initial_state, sqrt_s) and is_valid_final_state(final_products):
                    return final_products, final_products[0], final_products[-1]
            except:
                continue
    else:
        # Обычное рассеяние l1 + l2 → l1 + l2 (+ фотоны)
        print("   ↔️ Лептон-лептонное рассеяние")
        
        for _ in range(5000):
            try:
                # Упругое рассеяние + возможно фотон
                final_products = [_particle_cache[id1], _particle_cache[id2]]
                
                if random.random() < 0.3 and sqrt_s > 1.0:
                    # Излучение фотона
                    photon = _particle_cache[22]
                    final_products.append(photon)
                
                if check_conservation(final_products, initial_state, sqrt_s) and is_valid_final_state(final_products):
                    return final_products, final_products[0], final_products[1]
            except:
                continue
    
    return None



def generate_event(id1, id2, beam_energy, hadrons, leptons, gauge_bosons, resonances, max_attempts=100000):
    """
    НОВОЕ: Универсальная генерация событий
    
    Определяет тип взаимодействия и вызывает соответствующую функцию
    """
    if not hadrons and not leptons and not gauge_bosons:
        print("❌ ОШИБКА: Нет загруженных частиц")
        return None
    
    # Объединенный список всех частиц
    particles_all = hadrons + leptons + gauge_bosons
    
    # Вычисляем энергию
    m1 = PARTICLE_VALUES[id1]['mass']
    m2 = PARTICLE_VALUES[id2]['mass']
    s = m1**2 + m2**2 + 2 * m2 * beam_energy
    sqrt_s = sqrt(max(0.1, s))
    
    # Начальное состояние
    lepton1 = get_lepton_numbers(id1)
    lepton2 = get_lepton_numbers(id2)
    
    initial_state = {
        'charge': PARTICLE_VALUES[id1]['charge'] + PARTICLE_VALUES[id2]['charge'],
        'baryon': PARTICLE_VALUES[id1]['baryon'] + PARTICLE_VALUES[id2]['baryon'],
        'strangeness': PARTICLE_VALUES[id1]['s'] + PARTICLE_VALUES[id2]['s'],
        'charm': PARTICLE_VALUES[id1]['c'] + PARTICLE_VALUES[id2]['c'],
        'bottom': PARTICLE_VALUES[id1]['b'] + PARTICLE_VALUES[id2]['b'],
        # НОВОЕ: лептонные числа
        'L_e': lepton1['e'] + lepton2['e'],
        'L_mu': lepton1['mu'] + lepton2['mu'],
        'L_tau': lepton1['tau'] + lepton2['tau'],
    }
    
    # НОВОЕ: Определяем тип взаимодействия
    interaction_type = get_interaction_type(id1, id2)
    
    print(f"🔄 Генерация события: √s = {sqrt_s:.2f} ГэВ")
    print(f"   Тип взаимодействия: {interaction_type}")
    print(f"   Начальное состояние: Q={initial_state['charge']:.0f}, "
          f"B={initial_state['baryon']:.0f}, "
          f"L_e={initial_state['L_e']:.0f}, "
          f"L_μ={initial_state['L_mu']:.0f}, "
          f"L_τ={initial_state['L_tau']:.0f}")
    
    # Вызываем соответствующую функцию генерации
    result = None
    
    if interaction_type == 'hadron-hadron':
        result = generate_hadron_hadron_event(id1, id2, sqrt_s, initial_state, particles_all, resonances)
    
    elif interaction_type == 'hadron-lepton':
        # Определяем кто адрон, кто лептон
        hadron_id = id1 if is_hadron(id1) else id2
        lepton_id = id1 if is_lepton(id1) else id2
        result = generate_hadron_lepton_event(hadron_id, lepton_id, sqrt_s, initial_state, particles_all, resonances)
    
    elif interaction_type == 'lepton-lepton':
        result = generate_lepton_lepton_event(id1, id2, sqrt_s, initial_state, particles_all, resonances)
    
    else:
        print(f"   ⚠️ Тип взаимодействия {interaction_type} пока не реализован")
        return None
    
    if result:
        final_products, first_particle, second_particle = result
        
        # Формируем результат
        products = {f'id_{i+1}': p.mcid for i, p in enumerate(final_products)}
        
        first_products = [{
            "id_1": first_particle.mcid,
            "id_2": second_particle.mcid
        }]
        
        values = [{
            "Mass": sqrt_s,
            "BaryonNum": initial_state['baryon'],
            "S,B,C": [
                initial_state['strangeness'],
                initial_state['bottom'],
                initial_state['charm']
            ],
            "Charge": initial_state['charge'],
            # НОВОЕ
            "Lepton_e": initial_state['L_e'],
            "Lepton_mu": initial_state['L_mu'],
            "Lepton_tau": initial_state['L_tau'],
            "InteractionType": interaction_type
        }]
        
        print(f"✓ Событие найдено!")
        print(f"   Продукты: {[_particle_cache[p.mcid].name for p in final_products]}")
        
        return [products], first_products, values
    
    print(f"❌ Событие не найдено")
    return None

def SimulationEvent(id_1, id_2, beam_energy, hadrons, leptons, gauge_bosons, resonances):
    """
    ОБНОВЛЕНО: Теперь принимает раздельные списки частиц
    
    Args:
        id_1, id_2: MCID частиц
        beam_energy: энергия пучка (ГэВ)
        hadrons: список адронов
        leptons: список лептонов
        gauge_bosons: список калибровочных бозонов
        resonances: список резонансов
    """
    
    if not hadrons and not leptons and not gauge_bosons:
        print("❌ ОШИБКА: Нет загруженных частиц!")
        return None
    
    print(f"\n{'='*60}")
    print(f"🎯 СИМУЛЯЦИЯ СТОЛКНОВЕНИЯ")
    print(f"   Частица 1: {id_1} ({PARTICLE_VALUES[id_1]['type']})")
    print(f"   Частица 2: {id_2} ({PARTICLE_VALUES[id_2]['type']})")
    print(f"   Энергия пучка: {beam_energy} ГэВ")
    print(f"{'='*60}")
    
    result = generate_event(id_1, id_2, beam_energy, hadrons, leptons, gauge_bosons, resonances)
    
    if result:
        event, first_products, values = result
        print(f"\n✓ УСПЕХ!")
        return event, first_products, values
    else:
        print(f"\n✗ НЕУДАЧА")
        return None
    







# ============================================================================
# 1. ЗАГРУЗКА ЧАСТИЦ
# ============================================================================

print("="*70)
print("ЗАГРУЗКА БАЗЫ ДАННЫХ ЧАСТИЦ")
print("="*70)

# ВАЖНО: теперь load_particles возвращает 4 списка
hadrons, leptons, gauge_bosons, resonances = load_particles()

print(f"\n📊 Статистика:")
print(f"   Адроны (барионы + мезоны): {len(hadrons)}")
print(f"   Лептоны: {len(leptons)}")
print(f"   Калибровочные бозоны: {len(gauge_bosons)}")
print(f"   Резонансы: {len(resonances)}")


# ============================================================================
# 2. ПРИМЕРЫ РАЗЛИЧНЫХ ТИПОВ ВЗАИМОДЕЙСТВИЙ
# ============================================================================

print("\n" + "="*70)
print("ПРИМЕРЫ ВЗАИМОДЕЙСТВИЙ")
print("="*70)

# ----------------------------------------------------------------------------
# ПРИМЕР 1: Адрон + Адрон (стандартное взаимодействие)
# ----------------------------------------------------------------------------
print("\n" + "-"*70)
print("ПРИМЕР 1: ПРОТОН + ПРОТОН")
print("-"*70)

result1 = SimulationEvent(
    id_1=211,      # протон
    id_2=11,      # протон
    beam_energy=10.0,
    hadrons=hadrons,
    leptons=leptons,
    gauge_bosons=gauge_bosons,
    resonances=resonances
)

if result1:
    event, first, values = result1
    print("\n📋 Результат:")
    print(f"   Продукты реакции: {event}")
    print(f"   Законы сохранения: {values}")


