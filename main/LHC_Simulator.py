import sys
import os
import pdg
import shutil
import random
from math import *
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
PARTICLE_VALUES = {}
RESONANCE_DECAYS = {}

LEPTON_NUM = {
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


def lepton_num(id):
    try:
        return LEPTON_NUM[id]
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
def get_lepton_numbers(mcid):
    """
    Получить лептонные числа частицы
    
    Returns:
        dict: {'e': L_e, 'mu': L_mu, 'tau': L_tau}
    """
    if mcid in LEPTON_NUM:
        return LEPTON_NUM[mcid]
    else:
        return {'e': 0, 'mu': 0, 'tau': 0}
    
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
    
@lru_cache(maxsize=1000)
def GetAnimationType(info): # info = [A, B, C, D]

    types = []
    names = []
    IType = ''

    for i in info:
        p = PARTICLE_VALUES[i]['type']
        if PARTICLE_VALUES[i]['Name'] is not None:
            n = PARTICLE_VALUES[i]['Name']
        types.append(p)
        names.append(n)

    if all(x in {"lepton"} for x in types):
        IType = "Muon Event"
    if "Higgs" in names:
        IType = "Higgs Boson"
    if "W" in names:
        IType = "W/Z Boson"
    if all(x in {"meson", "baryon", "hadron"} for x in types):
        IType = "Jet Event"
    else:
        IType = "Standard"
    
    return IType

    

        



            



# ============================================================================
# ЗАГРУЗКА ЧАСТИЦ (ОПТИМИЗИРОВАННАЯ)
# ============================================================================

def load_particles():
    """Быстрая загрузка частиц из базы данных"""
    print("% Загрузка частиц из базы...")
    particles = []
    resonances = []
    Type = ''
    # Получаем все частицы одним запросом
    all_pdgids = list(api.get_particles())
    
    #print(f"   Обработка {len(all_pdgids)} записей...")
    
    for i, pdg_entry in enumerate(all_pdgids):
        #if i % 100 == 0:
            #print(f"   Прогресс: {i}/{len(all_pdgids)}", end='\r')
        
        try:
            for particle in api.get(pdg_entry.pdgid):
                #if not (particle.is_baryon or particle.is_meson):
                    #continue
                if particle.mcid is None:
                    continue

                # Кэшируем частицу
                _particle_cache[particle.mcid] = particle
                if particle.is_baryon:
                    Type = 'baryon'
                elif particle.is_meson:
                    Type = 'meson'
                elif particle.is_lepton:
                    Type = 'lepton'
                elif particle.is_boson:
                    Type = 'boson'
                elif particle.is_quark:
                    Type = 'quark'

                lepton_nums = get_lepton_numbers(particle.mcid)

                name = particle.name if hasattr(particle, "name") else None

                PARTICLE_VALUES[particle.mcid] = {
                        "mass": safe_mass(particle),
                        "charge": safe_charge(particle),
                        "baryon": get_baryon_number(particle.mcid),
                        "s": get_quark_number(particle.mcid, "s"),
                        "c": get_quark_number(particle.mcid, "c"),
                        "b": get_quark_number(particle.mcid, "b"),
                        "J": particle.quantum_J,
                        "L_e": lepton_nums['e'],
                        "L_mu": lepton_nums['mu'],
                        "L_tau": lepton_nums['tau'],

                        "type": Type,
                        "Name": name
                    }
                
                # Разделяем на частицы и резонансы
                if is_resonance(particle.name) or (particle.width and particle.width > 0):
                    resonances.append(particle)
                    bf = api.get_particle_by_name(particle.name).exclusive_branching_fractions()
                    if bf:
                        RESONANCE_DECAYS[particle.mcid] = bf
                else:
                    particles.append(particle)
        except BaseException as es:
            print(es)
            continue
    
    print(f"\n$ Загружено {len(particles)} частиц, {len(resonances)} резонансов")
    return particles, resonances


# ============================================================================
# ВЫЧИСЛЕНИЕ ВЕСОВ (ОПТИМИЗИРОВАНО)
# ============================================================================

def calculate_temperature(sqrt_s):

    T_base = TEMPERATURE_SCALE
    
    if sqrt_s < 5.0:
        return T_base * 0.8
    elif sqrt_s < 20.0:
        return T_base * (0.8 + 0.1 * (sqrt_s - 5.0) / 15.0)
    else:
        return T_base * 1.2


def generate_weight(particle, sqrt_s, interaction_type='hadron-hadron'):
    
    m = safe_mass(particle)
    
    # Быстрые фильтры
    if m > sqrt_s * MAX_MASS_FRACTION:
        return 0.0
    
    try:
        T = 0.16
        gamma_s = 0.3
        gamma_c = 0.001
        
        J = particle.quantum_J
        
        # Базовый вес
        if (particle.is_baryon or particle.is_meson):
            quarks = get_particle_quarks(particle.mcid)
            n_s = quarks.count('s') + quarks.count('S')
            n_c = quarks.count('c') + quarks.count('C')
            weight = (2 * J + 1) * exp(-m / T) * (gamma_s ** n_s) * (gamma_c ** n_c)
            
            # Усиление для протонов и нейтронов
            if particle.mcid in [2212, 2112]:
                weight *= 5
        
        elif particle.is_lepton:
            # Лептоны легче рождаются
            weight = (2 * J + 1) * exp(-m / T) * 2.0
        
        elif particle.is_boson:
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
            if (particle.is_baryon or particle.is_meson):
                weight *= 2.0  # адроны рождаются чаще
        
        elif interaction_type == 'lepton-lepton':
            # e+e- → μ+μ-, τ+τ-, адроны
            if particle.is_lepton:
                weight *= 3.0
            elif particle.is_boson and particle.mcid == 22:
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
# ПРОВЕРКА ЗАКОНОВ СОХРАНЕНИЯ (ОПТИМИЗИРОВАНО)
# ============================================================================

def check_conservation(particles, initial_state, sqrt_s):
    """
    Быстрая проверка законов сохранения
    """
    # Создание массивов нужных свойств
    masses = np.array([PARTICLE_VALUES[p.mcid]['mass'] for p in particles])
    charges = np.array([PARTICLE_VALUES[p.mcid]['charge'] for p in particles])
    baryons = np.array([PARTICLE_VALUES[p.mcid]['baryon'] for p in particles])
    strangenesses = np.array([PARTICLE_VALUES[p.mcid]['s'] for p in particles])
    charms = np.array([PARTICLE_VALUES[p.mcid]['c'] for p in particles])
    bottoms = np.array([PARTICLE_VALUES[p.mcid]['b'] for p in particles])
    L_e = np.array([PARTICLE_VALUES[p.mcid]['L_e'] for p in particles])
    L_mu = np.array([PARTICLE_VALUES[p.mcid]['L_mu'] for p in particles])
    L_tau = np.array([PARTICLE_VALUES[p.mcid]['L_tau'] for p in particles])
    
    # Выполняем суммирование
    total_mass = np.sum(masses)
    final_state = {
        'charge': np.sum(charges),
        'baryon': np.sum(baryons),
        'strangeness': np.sum(strangenesses),
        'charm': np.sum(charms),
        'bottom': np.sum(bottoms),
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
    return True #all(p.is_baryon or p.is_meson for p in particles)

def get_interaction_type(id1, id2):

    type1 = PARTICLE_VALUES[id1]['type']
    type2 = PARTICLE_VALUES[id2]['type']
    
    types = {type1, type2}
    
    # Адрон + Адрон
    if types <= {'baryon', 'meson'}:
        print('hh')
        return 'hadron-hadron'
    
    
    # Адрон + Лептон (глубоконеупругое рассеяние)
    if types == {'baryon', 'lepton'} or types == {'meson', 'lepton'}:
        print('hl')
        return 'hadron-lepton'
    
    # Лептон + Лептон
    if types == {'lepton'}:
        print('ll')
        return 'lepton-lepton'
    
    # Адрон + Бозон
    if ('baryon' in types or 'meson' in types) and 'gauge_boson' in types:
        print('hb')
        return 'hadron-boson'
    
    # Лептон + Бозон
    if types == {'lepton', 'gauge_boson'}:
        print('hh')
        return 'lb'
    
    return 'unknown'

def generate_hadron_hadron_event(id1, id2, sqrt_s, initial_state, particles_all, resonances):

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

    # Получаем кварковую структуру адрона
    hadron_quarks = get_particle_quarks(hadron_id)
    if not hadron_quarks:
        return None
    
    print(f"   Кварки адрона: {hadron_quarks}")

    # Фильтруем возможные кварковые состояния заранее,
    # выбирая только одиночные кварки и мезоны
    quark_particles = [
        p for p in particles_all
        if len(get_particle_quarks(p.mcid)) <= 2
    ]

    if not quark_particles:
        print("   ⚠️ Нет доступных кварковых состояний")
        return None

    # Количество попыток генерации события
    max_attempts = 5000

    while max_attempts > 0:
        try:
            # Случайно генерируем число фрагментов (от 2 до 3)
            n_fragments = random.randint(2, 3)
            fragments = random.sample(quark_particles, n_fragments)
        
            # Генератор случайного числа для выбора поведения лептона
            rand_num = random.random()
        
            # Если вероятность меньше 0.7, сохраняем лептон как начальный
            if rand_num < 0.7:
                lepton_final = [_particle_cache[lepton_id]]
            else:
                # Иначе создаём пару лептон-анти-лептон
                anti_lepton_id = -lepton_id
                if anti_lepton_id in PARTICLE_VALUES:
                    lepton_final = [_particle_cache[lepton_id], _particle_cache[anti_lepton_id]]
                else:
                    lepton_final = [_particle_cache[lepton_id]]
                
            # Объединяем фрагменты и лептонные продукты
            final_products = fragments + lepton_final
        
            # Проверяем сохранение энергии и зарядов
            if check_conservation(final_products, initial_state, sqrt_s) \
               and is_valid_final_state(final_products):
                return final_products, fragments[0], _particle_cache[lepton_id]
        except Exception as e:
            pass  # Продолжаем попытки даже при исключениях
        
        max_attempts -= 1
    
    return None

def generate_lepton_lepton_event(id1, id2, sqrt_s, initial_state, particles_all, resonances):
    
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
                    hadrons = [p for p in particles_all if (p.is_baryon or p.is_meson)]
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


def generate_event(id1, id2, beam_energy, particles_list, resonances, max_attempts=100000):
    
    # ИСПРАВЛЕНИЕ: проверка входных данных
    if not particles_list or not resonances:
        print("❌ ОШИБКА: Пустые списки частиц или резонансов")
        return None
    
    #A = api.get_particle_by_mcid(id1)
    #B = api.get_particle_by_mcid(id2)
    # Вычисляем энергию центра масс
    m1 = PARTICLE_VALUES[id1]['mass']
    m2 = PARTICLE_VALUES[id2]['mass']
    s = m1**2 + m2**2 + 2 * m2 * beam_energy
    sqrt_s = sqrt(max(0.1, s))
    
    # Квантовые числа начального состояния
    initial_state = {
        'charge': PARTICLE_VALUES[id1]['charge'] + PARTICLE_VALUES[id2]['charge'],
        'baryon': PARTICLE_VALUES[id1]['baryon'] + PARTICLE_VALUES[id2]['baryon'],
        'strangeness': PARTICLE_VALUES[id1]['s'] + PARTICLE_VALUES[id2]['s'],
        'charm': PARTICLE_VALUES[id1]['c'] + PARTICLE_VALUES[id2]['c'],
        'bottom': PARTICLE_VALUES[id1]['b'] + PARTICLE_VALUES[id2]['b'],
        'L_e': PARTICLE_VALUES[id1]['L_e'] + PARTICLE_VALUES[id2]['L_e'],
        'L_mu': PARTICLE_VALUES[id1]['L_mu'] + PARTICLE_VALUES[id2]['L_mu'],
        'L_tau': PARTICLE_VALUES[id1]['L_tau'] + PARTICLE_VALUES[id2]['L_tau'],
    }


    E1 = sqrt(beam_energy**2 + m1**2)
    E2 = sqrt(beam_energy**2 + m2**2)

    tracks_count = int(PARTICLE_VALUES[id1]['charge']) + int(PARTICLE_VALUES[id2]['charge'] != 0)
    momentum = abs(E1 - E2)
    

    interaction_type = get_interaction_type(id1, id2)

    if interaction_type == 'hadron-hadron':
        result = generate_hadron_hadron_event(id1, id2, sqrt_s, initial_state, particles_list, resonances)
    
    elif interaction_type == 'hadron-lepton':
        # Определяем кто адрон, кто лептон
        hadron_id = id1 if (PARTICLE_VALUES[id1]['type'] == 'baryon' or PARTICLE_VALUES[id1]['type'] == 'meson') else id2
        lepton_id = id1 if PARTICLE_VALUES[id1]['type'] == 'lepton' else id2
        result = generate_hadron_lepton_event(hadron_id, lepton_id, sqrt_s, initial_state, particles_list, resonances)
    
    elif interaction_type == 'lepton-lepton':
        result = generate_lepton_lepton_event(id1, id2, sqrt_s, initial_state, particles_list, resonances)
    
    else:
        print(f"   ⚠️ Тип взаимодействия {interaction_type} пока не реализован")
        return None
    
    if result:
        final_products, first_particle, second_particle = result
        
        # Формируем результат
        products = {f'id_{i+1}': p.mcid for i, p in enumerate(final_products)}

        initial = [{'init_id1': id1, 'init_id2:': id2}]
        
        first_products = [{
            "id_1": first_particle.mcid,
            "id_2": second_particle.mcid
        }]

        AnimType = GetAnimationType(p.mcid for p in final_products)
        
        values = [{
            "Mass": sqrt_s,
            "BaryonNum": initial_state['baryon'],
            "S,B,C": [
                initial_state['strangeness'],
                initial_state['bottom'],
                initial_state['charm']
            ],
            "Charge": initial_state['charge'],
            
            "track_count": tracks_count,
            "momentum": momentum,
            "type": AnimType
        }]
        
        print(f"✓ Событие найдено!")
        print(f"   Продукты: {[_particle_cache[p.mcid].name for p in final_products]}")
        print(AnimType)
        
        return [products], first_products, values, initial
    
    print(f"Рассеяние")
    return [[{"id_1:": id1, "id_2:": id2}], [{"id_1:": id1, "id_2:": id2}], [{
            "Mass": sqrt_s,
            "BaryonNum": initial_state['baryon'],
            "S,B,C": [
                initial_state['strangeness'],
                initial_state['bottom'],
                initial_state['charm'] ], 
            "Charge": initial_state['charge'],

            "track_count": tracks_count,
            "momentum": momentum,
            "type": AnimType

            
        }], [{'init_id1': id1, 'init_id2:': id2}]]


    """# ОПТИМИЗАЦИЯ: предфильтруем резонансы по массе
    valid_resonances = [r for r in resonances if PARTICLE_VALUES[r.mcid]['mass'] < sqrt_s * 0.9]
    
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
    return None"""




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
        event, first_products, values, init = result
        print(f"\n✓ УСПЕХ! Событие сгенерировано")
        print(f"   Продукты реакции: {event}")
        print(f"   Первичные частицы: {first_products}")
        print(f"   Параметры: {values}")
        return event, first_products, values, init
    else:
        print(f"\n✗ НЕУДАЧА: Событие не сгенерировано")
        print(f"   Попробуйте:")
        print(f"   - Увеличить энергию пучка")
        print(f"   - Использовать другие начальные частицы")
        print(f"   - Проверить что списки частиц загружены корректно")
        return None
