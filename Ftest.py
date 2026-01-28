import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum

# ========== ТИПЫ ВЗАИМОДЕЙСТВИЙ ==========

class InteractionType(Enum):
    STRONG = "strong"       # сильное (глюоны)
    ELECTROWEAK = "ew"      # электрослабое (γ/W/Z)
    WEAK = "weak"           # слабое (W/Z)
    EM = "em"               # электромагнитное (γ)
    MIXED = "mixed"         # смешанное

# ========== БАЗОВЫЕ КЛАССЫ ДЛЯ ЧАСТИЦ ==========

@dataclass
class Particle:
    """Базовый класс для частиц"""
    name: str
    symbol: str
    charge: float  # в единицах элементарного заряда
    color: str = 'black'
    is_quark: bool = False
    is_lepton: bool = False
    is_boson: bool = False
    is_hadron: bool = False
    is_gluon: bool = False
    is_photon: bool = False
    is_weak_boson: bool = False
    
    def __post_init__(self):
        # Автоматически определяем некоторые свойства
        if self.symbol in ['g']:
            self.is_gluon = True
            self.is_boson = True
        elif self.symbol in ['γ', 'gamma']:
            self.is_photon = True
            self.is_boson = True
        elif self.symbol in ['W+', 'W-', 'Z']:
            self.is_weak_boson = True
            self.is_boson = True

@dataclass
class Quark(Particle):
    """Класс для кварков"""
    flavor: str = ''  # u, d, s, c, b, t
    is_quark: bool = True
    is_fermion: bool = True
    
    def __post_init__(self):
        # Цвета для кварков
        quark_colors = {
            'u': '#FF4444',  # красный
            'd': '#44FF44',  # зеленый
            's': '#4488FF',  # синий
            'c': '#FF44FF',  # маджента
            'b': '#AA44FF',  # фиолетовый
            't': '#FFAA44'   # оранжевый
        }
        self.color = quark_colors.get(self.flavor.lower(), '#000000')
        
        # Антикварки
        if self.flavor.endswith('bar'):
            self.color = self.color + '80'  # добавляем прозрачность

@dataclass
class AntiQuark(Quark):
    """Класс для антикварков"""
    def __post_init__(self):
        super().__post_init__()
        self.color = self.color + '80'  # полупрозрачный цвет

@dataclass
class Hadron(Particle):
    """Класс для адронов"""
    quark_content: List[str] = None  # например ['u', 'u', 'd'] для протона
    is_hadron: bool = True
    
    def __post_init__(self):
        if self.quark_content is None:
            self.quark_content = []
        
        # Определяем цвет по первому кварку
        if self.quark_content:
            first_quark = self.quark_content[0].replace('bar', '')
            quark_colors = {
                'u': '#FF4444', 'd': '#44FF44', 's': '#4488FF',
                'c': '#FF44FF', 'b': '#AA44FF', 't': '#FFAA44'
            }
            self.color = quark_colors.get(first_quark, '#000000')

@dataclass 
class Boson(Particle):
    """Класс для бозонов"""
    boson_type: str = ''  # gluon, photon, W, Z
    is_boson: bool = True
    
    def __post_init__(self):
        boson_colors = {
            'gluon': '#FF8800',     # оранжевый
            'photon': '#FFFF00',    # желтый
            'W': '#AA00AA',         # фиолетовый
            'Z': '#884400'          # коричневый
        }
        self.color = boson_colors.get(self.boson_type, '#000000')

# ========== БАЗА ДАННЫХ ЧАСТИЦ ==========

class ParticleDatabase:
    """База данных частиц с правильными свойствами"""
    
    def __init__(self):
        self.particles = {}
        self._initialize_particles()
    
    def _initialize_particles(self):
        # ===== КВАРКИ =====
        quarks = [
            Quark(name="верхний кварк", symbol="u", charge=2/3, flavor="u"),
            Quark(name="нижний кварк", symbol="d", charge=-1/3, flavor="d"),
            Quark(name="странный кварк", symbol="s", charge=-1/3, flavor="s"),
            Quark(name="очарованный кварк", symbol="c", charge=2/3, flavor="c"),
            Quark(name="прелестный кварк", symbol="b", charge=-1/3, flavor="b"),
            Quark(name="истинный кварк", symbol="t", charge=2/3, flavor="t"),
        ]
        
        # Антикварки
        antiquarks = [
            AntiQuark(name="анти-u", symbol="ū", charge=-2/3, flavor="ubar"),
            AntiQuark(name="анти-d", symbol="d̄", charge=1/3, flavor="dbar"),
            AntiQuark(name="анти-s", symbol="s̄", charge=1/3, flavor="sbar"),
        ]
        
        # ===== АДРОНЫ =====
        hadrons = [
            # Протон: uud
            Hadron(name="протон", symbol="p", charge=1, quark_content=['u', 'u', 'd']),
            # Нейтрон: udd
            Hadron(name="нейтрон", symbol="n", charge=0, quark_content=['u', 'd', 'd']),
            # Пион+: ud̄
            Hadron(name="π⁺", symbol="π⁺", charge=1, quark_content=['u', 'dbar']),
            # Пион-: ūd
            Hadron(name="π⁻", symbol="π⁻", charge=-1, quark_content=['ubar', 'd']),
            # Пион0: комбинация uū и dd̄
            Hadron(name="π⁰", symbol="π⁰", charge=0, quark_content=['u', 'ubar']),
            # Каон+: us̄
            Hadron(name="K⁺", symbol="K⁺", charge=1, quark_content=['u', 'sbar']),
        ]
        
        # ===== ЛЕПТОНЫ =====
        leptons = [
            Particle(name="электрон", symbol="e⁻", charge=-1, color="#0000FF", is_lepton=True),
            Particle(name="позитрон", symbol="e⁺", charge=1, color="#0000FF", is_lepton=True),
            Particle(name="мюон", symbol="μ⁻", charge=-1, color="#00AA00", is_lepton=True),
            Particle(name="антимюон", symbol="μ⁺", charge=1, color="#00AA00", is_lepton=True),
            Particle(name="тау", symbol="τ⁻", charge=-1, color="#FF0000", is_lepton=True),
            Particle(name="антитау", symbol="τ⁺", charge=1, color="#FF0000", is_lepton=True),
            Particle(name="электронное нейтрино", symbol="νₑ", charge=0, color="#888888", is_lepton=True),
            Particle(name="анти-νₑ", symbol="ν̄ₑ", charge=0, color="#888888", is_lepton=True),
        ]
        
        # ===== БОЗОНЫ =====
        bosons = [
            Boson(name="глюон", symbol="g", charge=0, boson_type="gluon"),
            Boson(name="фотон", symbol="γ", charge=0, boson_type="photon"),
            Boson(name="W⁺ бозон", symbol="W⁺", charge=1, boson_type="W"),
            Boson(name="W⁻ бозон", symbol="W⁻", charge=-1, boson_type="W"),
            Boson(name="Z бозон", symbol="Z", charge=0, boson_type="Z"),
        ]
        
        # Добавляем все частицы в словарь
        for particle_list in [quarks, antiquarks, hadrons, leptons, bosons]:
            for particle in particle_list:
                self.particles[particle.symbol] = particle
    
    def get_particle(self, symbol: str) -> Particle:
        """Получить частицу по символу"""
        # Некоторые альтернативные обозначения
        aliases = {
            'p+': 'p', 'proton': 'p',
            'n0': 'n', 'neutron': 'n',
            'pi+': 'π⁺', 'pi-': 'π⁻', 'pi0': 'π⁰',
            'w+': 'W⁺', 'w-': 'W⁻',
            'gamma': 'γ', 'photon': 'γ',
            'gluon': 'g',
            'e-': 'e⁻', 'e+': 'e⁺',
            'mu-': 'μ⁻', 'mu+': 'μ⁺',
        }
        
        symbol = aliases.get(symbol.lower(), symbol)
        
        if symbol in self.particles:
            return self.particles[symbol]
        else:
            # Если частица не найдена, создаем простую
            return Particle(name=symbol, symbol=symbol, charge=0, color='black')

# ========== КЛАСС ДЛЯ ВЕРШИН И ЛИНИЙ ==========

@dataclass
class Vertex:
    """Вершина взаимодействия"""
    x: float
    y: float
    particles_in: List[str] = None
    particles_out: List[str] = None
    interaction: str = ""
    
    def __post_init__(self):
        if self.particles_in is None:
            self.particles_in = []
        if self.particles_out is None:
            self.particles_out = []

@dataclass
class ParticleLine:
    """Линия частицы на диаграмме"""
    start: Tuple[float, float]
    end: Tuple[float, float]
    particle: Particle
    is_incoming: bool = True
    style: str = "solid"  # solid, dashed, wavy, curly
    label_pos: float = 0.5  # положение метки (0-1)

# ========== ОСНОВНОЙ КЛАСС ДИАГРАММЫ ==========

class FeynmanDiagram:
    """Улучшенный класс для создания диаграмм Фейнмана"""
    
    def __init__(self, cm_energy: float = 1000.0, width: float = 12, height: float = 8):
        self.cm_energy = cm_energy
        self.db = ParticleDatabase()
        self.fig, self.ax = plt.subplots(figsize=(width, height))
        self.lines = []
        self.vertices = []
        self.time_direction = 'right'
        
        # Цвета для разных типов линий
        self.style_colors = {
            'quark': {'color': '#FF4444', 'alpha': 1.0},
            'antiquark': {'color': '#4444FF', 'alpha': 0.7},
            'gluon': {'color': '#FF8800', 'alpha': 0.8},
            'photon': {'color': '#FFFF00', 'alpha': 0.8},
            'weak': {'color': '#AA00AA', 'alpha': 0.8},
            'lepton': {'color': '#0000FF', 'alpha': 0.8},
        }
    
    def create_collision(self, 
                        reaction_str: str,
                        interaction_type: InteractionType = InteractionType.STRONG,
                        show_labels: bool = True,
                        title: str = None):
        """
        Создать диаграмму по строке реакции
        
        Parameters:
        -----------
        reaction_str: строка реакции, например "p + p → p + n + π⁺"
        interaction_type: тип взаимодействия
        show_labels: показывать ли метки частиц
        title: заголовок диаграммы
        """
        # Парсим строку реакции
        if '→' in reaction_str:
            parts = reaction_str.split('→')
        elif '->' in reaction_str:
            parts = reaction_str.split('->')
        else:
            raise ValueError("Неверный формат реакции. Используйте '→' или '->'")
        
        # Убираем пробелы и разбиваем на частицы
        incoming_str = parts[0].strip()
        outgoing_str = parts[1].strip()
        
        # Разделяем частицы
        incoming_particles = []
        for token in incoming_str.replace('+', ' ').split():
            if token.strip():
                incoming_particles.append(self.db.get_particle(token.strip()))
        
        outgoing_particles = []
        for token in outgoing_str.replace('+', ' ').split():
            if token.strip():
                outgoing_particles.append(self.db.get_particle(token.strip()))
        
        # Очищаем диаграмму
        self.ax.clear()
        self.lines = []
        self.vertices = []
        
        # Настраиваем оси
        self.ax.set_xlim(-1, 10)
        self.ax.set_ylim(-3, 3)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        # Заголовок
        if title:
            self.ax.set_title(title, fontsize=16, pad=20, fontweight='bold')
        else:
            self.ax.set_title(f"Диаграмма Фейнмана: {reaction_str}\nE_cm = {self.cm_energy} ГэВ", 
                            fontsize=14, pad=20)
        
        # Определяем тип столкновения и рисуем
        if any(p.is_hadron for p in incoming_particles):
            self._draw_hadron_collision_improved(incoming_particles, outgoing_particles, interaction_type)
        else:
            self._draw_elementary_collision(incoming_particles, outgoing_particles, interaction_type)
        
        # Добавляем легенду
        if show_labels:
            self._add_legend()
        
        # Стрелка времени
        self._add_time_arrow()
        
        plt.tight_layout()
    
    def _draw_hadron_collision_improved(self, incoming, outgoing, interaction_type):
        """Улучшенная отрисовка адронного столкновения с непрерывными линиями"""
        # Начальные координаты для входящих адронов
        start_x = 0
        y_spacing = 0.3
        
        # ===== ВХОДЯЩИЕ АДРОНЫ =====
        y_offset_in = 1.0
        
        # Первый адрон (вверху)
        if len(incoming) > 0:
            in1 = incoming[0]
            if in1.is_hadron:
                # Рисуем кварковые линии как НЕПРЕРЫВНЫЕ линии от начала до области взаимодействия
                quark_y_positions = []
                for i, quark_sym in enumerate(getattr(in1, 'quark_content', ['q'])):
                    y_pos = y_offset_in - i * y_spacing
                    quark_y_positions.append(y_pos)
                    
                    # Линия кварка от начала до области взаимодействия
                    self._draw_quark_line(
                        start=(start_x, y_pos),
                        end=(3.5, y_pos),  # Область взаимодействия
                        quark_type=quark_sym,
                        label=f"{quark_sym}" if i == 0 else ""
                    )
                
                # Обозначение адрона в начале
                self.ax.text(start_x - 0.5, y_offset_in + 0.2, 
                           in1.symbol, fontsize=12, fontweight='bold',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="#E6F3FF", alpha=0.8))
        
        # Второй адрон (внизу)
        if len(incoming) > 1:
            in2 = incoming[1]
            if in2.is_hadron:
                quark_y_positions2 = []
                for i, quark_sym in enumerate(getattr(in2, 'quark_content', ['q'])):
                    y_pos = -y_offset_in + i * y_spacing
                    quark_y_positions2.append(y_pos)
                    
                    self._draw_quark_line(
                        start=(start_x, y_pos),
                        end=(3.5, y_pos),
                        quark_type=quark_sym,
                        label=f"{quark_sym}" if i == 0 else ""
                    )
                
                self.ax.text(start_x - 0.5, -y_offset_in - 0.2, 
                           in2.symbol, fontsize=12, fontweight='bold',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="#E6F3FF", alpha=0.8))
        
        # ===== ОБЛАСТЬ ВЗАИМОДЕЙСТВИЯ =====
        int_center_x = 4.0
        int_width = 1.0
        int_height = 2.5
        
        # Рисуем область взаимодействия
        interaction_box = mpatches.Rectangle(
            (int_center_x - int_width/2, -int_height/2),
            int_width, int_height,
            facecolor='#F0F0F0', edgecolor='#666666', linewidth=1.5,
            alpha=0.6, linestyle='--'
        )
        self.ax.add_patch(interaction_box)
        
        # Текст в области взаимодействия
        int_text = {
            InteractionType.STRONG: "Сильное\nвзаимодействие\n(глюоны)",
            InteractionType.ELECTROWEAK: "Электрослабое\nвзаимодействие",
            InteractionType.WEAK: "Слабое\nвзаимодействие\n(W/Z)",
            InteractionType.EM: "ЭМ взаимодействие\n(фотоны)",
        }.get(interaction_type, "Взаимодействие")
        
        self.ax.text(int_center_x, 0, int_text, 
                    fontsize=10, ha='center', va='center',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9))
        
        # ===== БОЗОНЫ В ОБЛАСТИ ВЗАИМОДЕЙСТВИЯ =====
        # Автоматически добавляем бозоны в зависимости от типа взаимодействия
        boson_y = 0.8
        if interaction_type == InteractionType.STRONG:
            # Глюоны внутри области
            self._draw_gluon_line(
                start=(int_center_x - 0.3, boson_y),
                end=(int_center_x + 0.3, boson_y),
                label="g"
            )
        elif interaction_type in [InteractionType.WEAK, InteractionType.ELECTROWEAK]:
            # W/Z бозоны
            self._draw_weak_boson_line(
                start=(int_center_x - 0.3, boson_y),
                end=(int_center_x + 0.3, boson_y),
                label="W/Z"
            )
        elif interaction_type == InteractionType.EM:
            # Фотоны
            self._draw_photon_line(
                start=(int_center_x - 0.3, boson_y),
                end=(int_center_x + 0.3, boson_y),
                label="γ"
            )
        
        # ===== ВЫХОДЯЩИЕ ЧАСТИЦЫ =====
        out_start_x = int_center_x + int_width/2
        out_end_x = 9.0
        
        n_out = len(outgoing)
        if n_out > 0:
            # Распределяем по вертикали
            y_positions = np.linspace(-1.5, 1.5, n_out)
            
            for i, (particle, y_pos) in enumerate(zip(outgoing, y_positions)):
                # Определяем, нужно ли рисовать W-бозон
                draw_w_boson = False
                w_label = None
                
                # Проверяем, участвует ли в слабом взаимодействии
                if particle.symbol in ['π⁺', 'π⁻', 'K⁺', 'K⁻']:
                    draw_w_boson = True
                    w_label = 'W⁺' if particle.charge > 0 else 'W⁻'
                
                if draw_w_boson and w_label:
                    # Промежуточная точка для W-бозона
                    w_x = (out_start_x + out_end_x) / 2 - 1
                    
                    # Линия от области к W-бозону
                    self._draw_quark_line(
                        start=(out_start_x, 0),
                        end=(w_x, y_pos),
                        quark_type='u' if particle.charge > 0 else 'd',
                        label=""
                    )
                    
                    # W-бозон
                    self._draw_weak_boson_line(
                        start=(w_x, y_pos),
                        end=(w_x + 1.0, y_pos),
                        label=w_label,
                        is_external=True
                    )
                    
                    # Линия от W-бозона к конечной частице
                    self._draw_quark_line(
                        start=(w_x + 1.0, y_pos),
                        end=(out_end_x, y_pos),
                        quark_type='d' if particle.charge > 0 else 'u',
                        label=""
                    )
                else:
                    # Прямая линия к частице
                    if particle.is_hadron:
                        # Для адронов рисуем несколько кварковых линий
                        for j, quark_sym in enumerate(getattr(particle, 'quark_content', ['q'])):
                            q_y = y_pos + (j - len(getattr(particle, 'quark_content', ['q']))/2 + 0.5) * 0.2
                            self._draw_quark_line(
                                start=(out_start_x, 0 if j == 0 else q_y),  # Все начинаются из центра
                                end=(out_end_x, q_y),
                                quark_type=quark_sym,
                                label=f"{quark_sym}" if j == 0 else ""
                            )
                    else:
                        # Для элементарных частиц
                        self._draw_particle_line(
                            start=(out_start_x, 0),
                            end=(out_end_x, y_pos),
                            particle=particle,
                            is_incoming=False
                        )
                
                # Обозначение частицы в конце
                bbox_props = dict(boxstyle="round,pad=0.3", facecolor="#FFE6E6", alpha=0.8)
                if particle.is_hadron:
                    bbox_props['facecolor'] = "#E6FFE6"
                
                self.ax.text(out_end_x + 0.3, y_pos, particle.symbol,
                           fontsize=12, fontweight='bold', va='center',
                           bbox=bbox_props)
    
    def _draw_elementary_collision(self, incoming, outgoing, interaction_type):
        """Отрисовка столкновения элементарных частиц"""
        # Центральная вершина
        v_center = (3, 0)
        
        # Входящие частицы
        in_angle = np.pi/4
        for i, particle in enumerate(incoming):
            angle = in_angle if i == 0 else -in_angle
            length = 3
            
            start_x = v_center[0] - length * np.cos(angle)
            start_y = v_center[1] - length * np.sin(angle)
            
            self._draw_particle_line(
                start=(start_x, start_y),
                end=v_center,
                particle=particle,
                is_incoming=True
            )
        
        # Исходящие частицы
        n_out = len(outgoing)
        if n_out > 0:
            angles = np.linspace(-np.pi/3, np.pi/3, n_out)
            for i, (particle, angle) in enumerate(zip(outgoing, angles)):
                length = 3
                end_x = v_center[0] + length * np.cos(angle)
                end_y = v_center[1] + length * np.sin(angle)
                
                self._draw_particle_line(
                    start=v_center,
                    end=(end_x, end_y),
                    particle=particle,
                    is_incoming=False
                )
        
        # Вершина взаимодействия
        self.ax.plot(v_center[0], v_center[1], 'ko', markersize=12, zorder=10)
        
        # Тип взаимодействия в вершине
        vertex_label = {
            InteractionType.STRONG: "g",
            InteractionType.WEAK: "W/Z",
            InteractionType.EM: "γ",
            InteractionType.ELECTROWEAK: "γ/W/Z"
        }.get(interaction_type, "int")
        
        self.ax.text(v_center[0], v_center[1] + 0.3, vertex_label,
                    fontsize=11, ha='center', va='bottom', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    def _draw_quark_line(self, start, end, quark_type, label=""):
        """Нарисовать линию кварка"""
        x1, y1 = start
        x2, y2 = end
        
        # Определяем цвет кварка
        quark_colors = {
            'u': '#FF4444', 'd': '#44FF44', 's': '#4488FF',
            'c': '#FF44FF', 'b': '#AA44FF', 't': '#FFAA44',
            'ubar': '#FF8888', 'dbar': '#88FF88', 'sbar': '#8888FF',
            'q': '#666666'  # общий кварк
        }
        
        color = quark_colors.get(quark_type, '#666666')
        
        # Рисуем линию
        line = self.ax.plot([x1, x2], [y1, y2], 
                          color=color, linewidth=2.5, solid_capstyle='round',
                          alpha=0.9, zorder=2)[0]
        
        # Добавляем стрелку (только если линия достаточно длинная)
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx**2 + dy**2)
        
        if length > 0.5:
            # Стрелка посередине
            arrow_pos = 0.5
            arrow_x = x1 + arrow_pos * dx
            arrow_y = y1 + arrow_pos * dy
            
            # Направление стрелки
            if x2 > x1:  # движение вправо
                self.ax.annotate('', xy=(arrow_x + 0.1*dx/length, arrow_y + 0.1*dy/length),
                               xytext=(arrow_x - 0.1*dx/length, arrow_y - 0.1*dy/length),
                               arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
        
        # Метка кварка
        if label:
            label_x = (x1 + x2) / 2
            label_y = (y1 + y2) / 2 + 0.1
            
            # Для антикварков добавляем черту
            display_label = f"${'\\bar{' + quark_type[0] + '}' if 'bar' in quark_type else quark_type}$"
            
            self.ax.text(label_x, label_y, display_label, fontsize=9,
                        color=color, ha='center', va='bottom', fontweight='bold')
        
        return line
    
    def _draw_particle_line(self, start, end, particle, is_incoming=True):
        """Нарисовать линию элементарной частицы"""
        x1, y1 = start
        x2, y2 = end
        
        # Стиль линии
        if particle.is_lepton:
            linestyle = '--'
            linewidth = 2.0
        else:
            linestyle = '-'
            linewidth = 2.0
        
        # Рисуем линию
        line = self.ax.plot([x1, x2], [y1, y2], 
                          color=particle.color, linewidth=linewidth,
                          linestyle=linestyle, alpha=0.9, zorder=2)[0]
        
        # Стрелка
        dx, dy = x2 - x1, y2 - y1
        arrow_pos = 0.6 if is_incoming else 0.4
        
        arrow_x = x1 + arrow_pos * dx
        arrow_y = y1 + arrow_pos * dy
        
        self.ax.annotate('', xy=(arrow_x + 0.05*dx, arrow_y + 0.05*dy),
                       xytext=(arrow_x - 0.05*dx, arrow_y - 0.05*dy),
                       arrowprops=dict(arrowstyle='->', color=particle.color, lw=1.5))
        
        # Метка частицы
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Смещаем метку для лучшей читаемости
        if abs(dy) < 0.1:
            label_y = mid_y + 0.15
        else:
            label_y = mid_y + 0.1 * np.sign(dy)
        
        self.ax.text(mid_x, label_y, particle.symbol, fontsize=10,
                    color=particle.color, ha='center', va='center',
                    fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", 
                            edgecolor=particle.color, alpha=0.8))
        
        return line
    
    def _draw_gluon_line(self, start, end, label="g"):
        """Нарисовать волнистую линию глюона"""
        x1, y1 = start
        x2, y2 = end
        
        # Создаем волнистую линию
        t = np.linspace(0, 1, 200)
        
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx**2 + dy**2)
        
        # Перпендикулярный вектор
        if abs(dy) < 0.01:
            perp_x, perp_y = 0, 1
        else:
            perp_x, perp_y = -dy, dx
            norm = np.sqrt(perp_x**2 + perp_y**2)
            perp_x, perp_y = perp_x/norm, perp_y/norm
        
        # Волны
        wave_amplitude = 0.15
        wave_frequency = 15
        
        x_wave = x1 + dx * t + perp_x * wave_amplitude * np.sin(wave_frequency * np.pi * t)
        y_wave = y1 + dy * t + perp_y * wave_amplitude * np.sin(wave_frequency * np.pi * t)
        
        self.ax.plot(x_wave, y_wave, color='#FF8800', linewidth=3, alpha=0.8, zorder=3)
        
        # Метка
        mid_idx = 100
        self.ax.text(x_wave[mid_idx], y_wave[mid_idx] + 0.15, label,
                    fontsize=10, color='#FF8800', ha='center', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9))
    
    def _draw_weak_boson_line(self, start, end, label="W", is_external=False):
        """Нарисовать линию слабого бозона"""
        x1, y1 = start
        x2, y2 = end
        
        # Для внешних W-бозонов делаем волнистые линии
        if is_external:
            t = np.linspace(0, 1, 150)
            dx, dy = x2 - x1, y2 - y1
            
            if abs(dy) < 0.01:
                perp_x, perp_y = 0, 1
            else:
                perp_x, perp_y = -dy, dx
                norm = np.sqrt(perp_x**2 + perp_y**2)
                perp_x, perp_y = perp_x/norm, perp_y/norm
            
            wave_amplitude = 0.12
            wave_frequency = 12
            
            x_wave = x1 + dx * t + perp_x * wave_amplitude * np.sin(wave_frequency * np.pi * t)
            y_wave = y1 + dy * t + perp_y * wave_amplitude * np.sin(wave_frequency * np.pi * t)
            
            line = self.ax.plot(x_wave, y_wave, color='#AA00AA', linewidth=2.5, 
                              alpha=0.9, zorder=4)[0]
            
            # Стрелка для W-бозона
            if dx > 0:  # движение вправо
                arrow_idx = 100
                self.ax.annotate('', 
                               xy=(x_wave[arrow_idx+5], y_wave[arrow_idx+5]),
                               xytext=(x_wave[arrow_idx-5], y_wave[arrow_idx-5]),
                               arrowprops=dict(arrowstyle='->', color='#AA00AA', lw=1.5))
        else:
            # Для внутренних - пунктир
            line = self.ax.plot([x1, x2], [y1, y2], color='#AA00AA', 
                              linewidth=2, linestyle=':', alpha=0.7, zorder=3)[0]
        
        # Метка
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        self.ax.text(mid_x, mid_y + 0.15, label, fontsize=10,
                    color='#AA00AA', ha='center', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9))
        
        return line
    
    def _draw_photon_line(self, start, end, label="γ"):
        """Нарисовать волнистую линию фотона"""
        # Аналогично gluon_line, но с другим цветом
        x1, y1 = start
        x2, y2 = end
        
        t = np.linspace(0, 1, 150)
        dx, dy = x2 - x1, y2 - y1
        
        if abs(dy) < 0.01:
            perp_x, perp_y = 0, 1
        else:
            perp_x, perp_y = -dy, dx
            norm = np.sqrt(perp_x**2 + perp_y**2)
            perp_x, perp_y = perp_x/norm, perp_y/norm
        
        wave_amplitude = 0.1
        wave_frequency = 10
        
        x_wave = x1 + dx * t + perp_x * wave_amplitude * np.sin(wave_frequency * np.pi * t)
        y_wave = y1 + dy * t + perp_y * wave_amplitude * np.sin(wave_frequency * np.pi * t)
        
        self.ax.plot(x_wave, y_wave, color='#FFFF00', linewidth=2.5, 
                    alpha=0.9, zorder=3)
        
        # Метка
        mid_idx = 75
        self.ax.text(x_wave[mid_idx], y_wave[mid_idx] + 0.15, label,
                    fontsize=10, color='#000000', ha='center', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9))
    
    def _add_legend(self):
        """Добавить информативную легенду"""
        legend_elements = [
            mpatches.Patch(color='#FF4444', label='u-кварк (верхний)'),
            mpatches.Patch(color='#44FF44', label='d-кварк (нижний)'),
            mpatches.Patch(color='#4488FF', label='s-кварк (странный)'),
            mpatches.Patch(color='#FF8800', label='Глюон (сильное)'),
            mpatches.Patch(color='#AA00AA', label='W/Z бозон (слабое)'),
            mpatches.Patch(color='#FFFF00', label='Фотон (ЭМ)'),
            mpatches.Patch(color='#0000FF', label='Лептоны', alpha=0.7),
        ]
        
        self.ax.legend(handles=legend_elements, 
                      loc='upper left', 
                      fontsize=9,
                      framealpha=0.95,
                      title="Обозначения частиц:")
    
    def _add_time_arrow(self):
        """Добавить стрелку времени"""
        self.ax.annotate('Время →', xy=(9.5, -2.7), xytext=(7.5, -2.7),
                        arrowprops=dict(arrowstyle='->', lw=2, color='red'),
                        fontsize=11, color='red', ha='center', fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    def save(self, filename: str = 'feynman_diagram.png', dpi: int = 300):
        """Сохранить диаграмму в файл"""
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        print(f"✓ Диаграмма сохранена в файл: {filename}")
    
    def show(self):
        """Показать диаграмму"""
        plt.show()

# ========== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ==========

def example_1():
    """Пример: p + p → p + n + π⁺ (с W⁺ бозоном)"""
    print("Пример 1: p + p → p + n + π⁺")
    print("Слабое взаимодействие через W⁺ бозон")
    print("=" * 60)
    
    diagram = FeynmanDiagram(cm_energy=2000.0, width=14, height=8)
    diagram.create_collision(
        reaction_str="p + p → p + n + π⁺",
        interaction_type=InteractionType.WEAK,
        title="Столкновение протонов с рождением пиона через W⁺ бозон"
    )
    
    diagram.save('proton_proton_collision_wplus.png')
    diagram.show()

def example_2():
    """Пример: u + d → u + d + g (сильное взаимодействие)"""
    print("\nПример 2: u + d → u + d + g")
    print("Сильное взаимодействие с глюоном")
    print("=" * 60)
    
    diagram = FeynmanDiagram(cm_energy=500.0)
    diagram.create_collision(
        reaction_str="u + d → u + d + g",
        interaction_type=InteractionType.STRONG,
        title="Кварк-кварковое рассеяние через глюон"
    )
    
    diagram.save('quark_quark_gluon.png')
    diagram.show()

def example_3():
    """Пример: e⁻ + e⁺ → μ⁻ + μ⁺ (электромагнитное)"""
    print("\nПример 3: e⁻ + e⁺ → μ⁻ + μ⁺")
    print("Электромагнитное взаимодействие")
    print("=" * 60)
    
    diagram = FeynmanDiagram(cm_energy=91.0)
    diagram.create_collision(
        reaction_str="e⁻ + e⁺ → μ⁻ + μ⁺",
        interaction_type=InteractionType.EM,
        title="Аннигиляция e⁻e⁺ в пару μ⁻μ⁺ через фотон"
    )
    
    diagram.save('electron_positron_annihilation.png')
    diagram.show()

def example_4():
    """Пример: p + n → p + n (упругое рассеяние)"""
    print("\nПример 4: p + n → p + n")
    print("Упругое рассеяние, сильное взаимодействие")
    print("=" * 60)
    
    diagram = FeynmanDiagram(cm_energy=1000.0, width=13, height=7)
    diagram.create_collision(
        reaction_str="p + n → p + n",
        interaction_type=InteractionType.STRONG,
        title="Упругое p-n рассеяние через обмен глюонами"
    )
    
    diagram.save('proton_neutron_elastic.png')
    diagram.show()

def custom_diagram():
    """Создание пользовательской диаграммы"""
    print("\n" + "=" * 60)
    print("СОЗДАНИЕ ПОЛЬЗОВАТЕЛЬСКОЙ ДИАГРАММЫ")
    print("=" * 60)
    
    print("\nДоступные форматы:")
    print("  p + p → p + n + π⁺")
    print("  u + d → u + d + g")
    print("  e⁻ + e⁺ → μ⁻ + μ⁺")
    print("  p + n → p + n")
    print("  и другие...")
    
    reaction = input("\nВведите реакцию (с '→' или '->'): ").strip()
    
    print("\nТипы взаимодействий:")
    print("  1. Сильное (глюоны)")
    print("  2. Слабое (W/Z бозоны)")
    print("  3. Электромагнитное (фотоны)")
    print("  4. Электрослабое")
    
    int_choice = input("Выберите тип взаимодействия (1-4): ").strip()
    int_map = {'1': InteractionType.STRONG, '2': InteractionType.WEAK,
               '3': InteractionType.EM, '4': InteractionType.ELECTROWEAK}
    interaction = int_map.get(int_choice, InteractionType.STRONG)
    
    energy = float(input("Энергия в с.ц.м. (ГэВ): ").strip() or "1000.0")
    
    title = input("Заголовок (Enter для авто): ").strip()
    
    filename = input("Имя файла для сохранения: ").strip() or "my_feynman_diagram.png"
    
    # Создаем диаграмму
    diagram = FeynmanDiagram(cm_energy=energy)
    
    if title:
        diagram.create_collision(reaction_str=reaction, interaction_type=interaction, title=title)
    else:
        diagram.create_collision(reaction_str=reaction, interaction_type=interaction)
    
    diagram.save(filename)
    diagram.show()

# ========== ГЛАВНОЕ МЕНЮ ==========

def main():
    """Главная функция с меню"""
    print("═" * 60)
    print("           ГЕНЕРАТОР ДИАГРАММ ФЕЙНМАНА v2.0")
    print("═" * 60)
    print("\nОсобенности новой версии:")
    print("  ✓ Непрерывные кварковые линии")
    print("  ✓ Правильное отображение W/Z бозонов")
    print("  ✓ Цветовое кодирование кварков")
    print("  ✓ Автоматическое определение взаимодействий")
    print("  ✓ Поддержка адронных и лептонных реакций")
    
    while True:
        print("\n" + "═" * 60)
        print("МЕНЮ:")
        print("  1. p + p → p + n + π⁺ (с W⁺ бозоном)")
        print("  2. u + d → u + d + g (глюонный обмен)")
        print("  3. e⁻ + e⁺ → μ⁻ + μ⁺ (аннигиляция)")
        print("  4. p + n → p + n (упругое рассеяние)")
        print("  5. Создать свою диаграмму")
        print("  6. Выход")
        
        choice = input("\nВыберите опцию (1-6): ").strip()
        
        if choice == '1':
            example_1()
        elif choice == '2':
            example_2()
        elif choice == '3':
            example_3()
        elif choice == '4':
            example_4()
        elif choice == '5':
            custom_diagram()
        elif choice == '6':
            print("\nВыход из программы. До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()