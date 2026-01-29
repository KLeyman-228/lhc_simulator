import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Circle, Arc

class HadronFeynmanDiagram:
    """
    Диаграммы Фейнмана для адронных взаимодействий
    с показом кварковой структуры
    """
    
    def __init__(self):
        self.colors = {
            'quark': {
                'u': '#FF6B6B',      # красный (up кварк)
                'd': '#4ECDC4',      # голубой (down кварк)  
                'ubar': '#FF9999',   # антикрасный
                'dbar': '#99FF99',   # антиголубой
            },
            'gluon': '#FFD166',      # желтый
            'pion': '#9D4EDD',       # фиолетовый
            'proton': '#118AB2',     # синий
            'neutron': '#06D6A0',    # зеленый
        }
    
    def draw_pp_scattering(self):
        """
        Диаграмма p+p → p+n+π⁺ с кварковой структурой
        Показывает обмен виртуальным пионом
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        
        # ===== Диаграмма 1: Полная адронная диаграма =====
        ax1.set_xlim(0, 10)
        ax1.set_ylim(0, 8)
        ax1.set_aspect('equal')
        ax1.set_title("Полная адронная диаграмма: p+p → p+n+π⁺", fontsize=14, fontweight='bold')
        
        # Входные протоны
        self._draw_hadron(ax1, 1, 6, 3.5, 6, 'p', direction='right', show_quarks=True)
        self._draw_hadron(ax1, 1, 2, 3.5, 2, 'p', direction='right', show_quarks=True)
        
        # Выходные частицы
        self._draw_hadron(ax1, 6.5, 6.5, 9, 6.5, 'p', direction='right', show_quarks=True)
        self._draw_hadron(ax1, 6.5, 3.5, 9, 3.5, 'n', direction='right', show_quarks=True)
        self._draw_hadron(ax1, 6.5, 1.5, 9, 1.5, 'π⁺', direction='right', show_quarks=False)
        
        # Обмен пионом
        self._draw_dashed_line(ax1, 3.5, 6, 6.5, 3.5, self.colors['pion'], 2)
        
        # Вершины взаимодействия
        ax1.scatter([3.5, 6.5], [6, 3.5], color='red', s=100, zorder=5, 
                   edgecolors='darkred', linewidth=2)
        
        # Подписи
        ax1.text(2.2, 6.3, 'p (uud)', fontsize=11, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue'))
        ax1.text(2.2, 1.7, 'p (uud)', fontsize=11, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue'))
        ax1.text(7.8, 6.8, 'p (uud)', fontsize=11, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen'))
        ax1.text(7.8, 3.3, 'n (udd)', fontsize=11, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow'))
        ax1.text(7.8, 1.3, 'π⁺ (uđ)', fontsize=11, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightpink'))
        
        ax1.text(5, 4.8, 'π⁺', fontsize=12, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor='purple'))
        
        ax1.axis('off')
        
        # ===== Диаграмма 2: Кварковая структура =====
        ax2.set_xlim(0, 12)
        ax2.set_ylim(0, 8)
        ax2.set_aspect('equal')
        ax2.set_title("Кварковая структура взаимодействия", fontsize=14, fontweight='bold')
        
        # Подробная кварковая диаграмма
        self._draw_quark_level_diagram(ax2)
        
        ax2.axis('off')
        
        plt.suptitle("Процесс p + p → p + n + π⁺ через однопионный обмен", 
                    fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        plt.show()
    
    def _draw_quark_level_diagram(self, ax):
        """Детальная кварковая диаграмма"""
        
        # ===== Входные протоны =====
        # Протон 1 (uud)
        ax.text(1, 7.2, 'Протон 1:', fontsize=11, ha='left', va='center')
        self._draw_quark(ax, 2.5, 7, 'u', 'quark')
        self._draw_quark(ax, 3.0, 7, 'u', 'quark')
        self._draw_quark(ax, 3.5, 7, 'd', 'quark')
        ax.text(4.2, 7, '→', fontsize=14, ha='center', va='center')
        
        # Протон 2 (uud)
        ax.text(1, 6.2, 'Протон 2:', fontsize=11, ha='left', va='center')
        self._draw_quark(ax, 2.5, 6, 'u', 'quark')
        self._draw_quark(ax, 3.0, 6, 'u', 'quark')
        self._draw_quark(ax, 3.5, 6, 'd', 'quark')
        ax.text(4.2, 6, '→', fontsize=14, ha='center', va='center')
        
        # ===== Взаимодействие =====
        ax.text(5, 6.8, 'Взаимодействие:', fontsize=11, ha='center', va='center',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow'))
        
        # Обмен u-кварком
        # d-кварк из протона 1 испускает виртуальный π⁺ (uđ)
        self._draw_quark_line(ax, 5.5, 7, 6.5, 5.5, 'd', direction='down')
        
        # π⁺ распадается на u и đ
        self._draw_dashed_line(ax, 6.5, 5.5, 8, 4.5, self.colors['pion'], 2)
        ax.text(7.2, 5.2, 'π⁺', fontsize=10, ha='center', va='center',
               bbox=dict(boxstyle="round,pad=0.2", facecolor='white'))
        
        # u-кварк из π⁺ поглощается d-кварком из протона 2
        self._draw_quark_line(ax, 8, 4.5, 8.5, 6, 'u', direction='up')
        
        # đ из π⁺ становится свободным
        self._draw_quark_line(ax, 8, 4.5, 9.5, 3.5, 'dbar', direction='right')
        
        # ===== Выходные частицы =====
        ax.text(10.5, 7.2, 'Выход:', fontsize=11, ha='center', va='center')
        
        # Протон (uud) - кварки не изменились
        ax.text(9.5, 6.8, 'Протон:', fontsize=10, ha='right', va='center')
        self._draw_quark(ax, 10, 7, 'u', 'quark')
        self._draw_quark(ax, 10.5, 7, 'u', 'quark')
        self._draw_quark(ax, 11, 7, 'd', 'quark')
        
        # Нейтрон (udd) - d превратился в u через поглощение π⁺
        ax.text(9.5, 5.8, 'Нейтрон:', fontsize=10, ha='right', va='center')
        self._draw_quark(ax, 10, 6, 'u', 'quark')
        self._draw_quark(ax, 10.5, 6, 'd', 'quark')
        self._draw_quark(ax, 11, 6, 'd', 'quark')
        ax.text(10.5, 5.5, 'd → u', fontsize=9, ha='center', va='center',
               bbox=dict(boxstyle="round,pad=0.2", facecolor='lightgreen'))
        
        # π⁺ (uđ) - свободный антикварк + кварк из другого источника
        ax.text(9.5, 4.3, 'π⁺ мезон:', fontsize=10, ha='right', va='center')
        self._draw_quark(ax, 10, 4, 'u', 'quark')
        self._draw_quark(ax, 10.5, 4, 'd', 'antiquark')
        
        # ===== Кварковые линии =====
        # Исходные u-кварки протонов остаются неизменными
        self._draw_quark_line(ax, 3.0, 7, 10, 7, 'u', direction='right', style='solid')
        self._draw_quark_line(ax, 2.5, 7, 10.5, 7, 'u', direction='right', style='solid')
        self._draw_quark_line(ax, 3.0, 6, 10, 6, 'u', direction='right', style='solid')
        
        # d-кварки
        self._draw_quark_line(ax, 3.5, 6, 10.5, 6, 'd', direction='right', style='solid')
        self._draw_quark_line(ax, 3.5, 6, 11, 6, 'd', direction='right', style='solid')
        
        # d-кварк из протона 1 превращается в u-кварк
        self._draw_quark_line(ax, 3.5, 7, 11, 6, 'd', direction='diagonal', style='dashed')
        ax.text(7.5, 6.3, 'd → u', fontsize=9, ha='center', va='center',
               bbox=dict(boxstyle="round,pad=0.2", facecolor='lightblue'))
        
        # Вершины
        ax.scatter([6.5, 8], [5.5, 4.5], color='red', s=80, zorder=5,
                  edgecolors='darkred', linewidth=2)
        
        # Объяснение процесса
        explanation = [
            "Процесс через однопионный обмен:",
            "1. d-кварк из протона 1 испускает виртуальный π⁺ (uđ)",
            "2. π⁺ поглощается d-кварком протона 2: d + π⁺ → u",
            "3. Протон 1 теряет заряд: p(uud) → n(udd)",  
            "4. Протон 2 получает заряд: p(uud) + π⁺ → p(uud) + π⁺",
            "5. Образуется свободный π⁺ мезон"
        ]
        
        for i, text in enumerate(explanation):
            ax.text(1, 1 + i*0.8, text, fontsize=10, ha='left', va='center',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    def _draw_hadron(self, ax, x1, y1, x2, y2, hadron_type, direction='right', show_quarks=False):
        """Рисует адрон с возможной кварковой структурой"""
        color = self.colors.get(hadron_type, 'gray')
        
        # Основная линия адрона
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=3, solid_capstyle='round')
        
        if show_quarks:
            # Показываем кварковый состав
            if hadron_type == 'p':  # протон (uud)
                offsets = [-0.15, 0, 0.15]
                colors = [self.colors['quark']['u'], self.colors['quark']['u'], self.colors['quark']['d']]
                labels = ['u', 'u', 'd']
            elif hadron_type == 'n':  # нейтрон (udd)
                offsets = [-0.15, 0, 0.15]
                colors = [self.colors['quark']['u'], self.colors['quark']['d'], self.colors['quark']['d']]
                labels = ['u', 'd', 'd']
            else:
                return
            
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            for i, (offset, color, label) in enumerate(zip(offsets, colors, labels)):
                qx = mid_x + offset
                qy = mid_y + 0.2
                circle = Circle((qx, qy), 0.1, facecolor=color, edgecolor='black', linewidth=1)
                ax.add_patch(circle)
                ax.text(qx, qy, label, fontsize=8, ha='center', va='center', fontweight='bold')
    
    def _draw_quark(self, ax, x, y, quark_type, particle_type='quark'):
        """Рисует отдельный кварк"""
        color = self.colors['quark'].get(quark_type, 'gray')
        
        if particle_type == 'antiquark':
            # Антикварк - квадрат
            rect = plt.Rectangle((x-0.15, y-0.15), 0.3, 0.3, 
                                facecolor=color, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
        else:
            # Кварк - круг
            circle = Circle((x, y), 0.15, facecolor=color, edgecolor='black', linewidth=1)
            ax.add_patch(circle)
        
        ax.text(x, y, quark_type, fontsize=10, ha='center', va='center', fontweight='bold')
    
    def _draw_quark_line(self, ax, x1, y1, x2, y2, quark_type, direction='right', style='solid'):
        """Рисует линию кварка"""
        color = self.colors['quark'].get(quark_type, 'gray')
        
        if style == 'dashed':
            ax.plot([x1, x2], [y1, y2], color=color, linewidth=2, linestyle='--', alpha=0.7)
        else:
            ax.plot([x1, x2], [y1, y2], color=color, linewidth=2, solid_capstyle='round')
        
        # Стрелка для направления
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx**2 + dy**2)
        if length > 0:
            dx, dy = dx/length, dy/length
            ax.arrow(x2 - dx*0.3, y2 - dy*0.3, dx*0.2, dy*0.2,
                    head_width=0.1, head_length=0.15, fc=color, ec=color)
    
    def _draw_dashed_line(self, ax, x1, y1, x2, y2, color, width=2):
        """Рисует пунктирную линию (для виртуальных частиц)"""
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=width, linestyle='--', alpha=0.8)

class HadronInteractionSimulator:
    """
    Симулятор адронных взаимодействий с кварковой физикой
    """
    
    def __init__(self):
        self.diagram = HadronFeynmanDiagram()
        
        # Кварковый состав адронов
        self.hadron_composition = {
            'p': {'quarks': ['u', 'u', 'd'], 'charge': +1, 'baryon_number': 1},
            'n': {'quarks': ['u', 'd', 'd'], 'charge': 0, 'baryon_number': 1},
            'π⁺': {'quarks': ['u', 'đ'], 'charge': +1, 'baryon_number': 0},
            'π⁻': {'quarks': ['d', 'ū'], 'charge': -1, 'baryon_number': 0},
            'π⁰': {'quarks': ['u', 'ū', 'd', 'đ'], 'charge': 0, 'baryon_number': 0},
        }
        
        # Возможные процессы
        self.processes = {
            'pp_pnpi': {
                'input': ['p', 'p'],
                'output': ['p', 'n', 'π⁺'],
                'description': 'p + p → p + n + π⁺ (однопионный обмен)',
                'min_energy': 1.2,  # ГэВ (порог ~1.08 ГэВ)
                'cross_section': 30,  # мб
            },
            'pp_pppi0': {
                'input': ['p', 'p'],
                'output': ['p', 'p', 'π⁰'],
                'description': 'p + p → p + p + π⁰',
                'min_energy': 1.35,
                'cross_section': 25,
            }
        }
    
    def check_conservation_laws(self, process_key):
        """Проверка законов сохранения для процесса"""
        process = self.processes[process_key]
        
        # Исходные квантовые числа
        initial_charge = sum(self.hadron_composition[h]['charge'] for h in process['input'])
        initial_baryon = sum(self.hadron_composition[h]['baryon_number'] for h in process['input'])
        
        # Конечные квантовые числа
        final_charge = sum(self.hadron_composition[h]['charge'] for h in process['output'])
        final_baryon = sum(self.hadron_composition[h]['baryon_number'] for h in process['output'])
        
        conservation = {
            'charge': initial_charge == final_charge,
            'baryon_number': initial_baryon == final_baryon,
        }
        
        return conservation
    
    def explain_quark_process(self, process_key):
        """Объяснение процесса на уровне кварков"""
        process = self.processes[process_key]
        
        print(f"\n🔬 КВАРКОВЫЙ АНАЛИЗ ПРОЦЕССА:")
        print(f"{process['description']}")
        print("-" * 50)
        
        if process_key == 'pp_pnpi':
            print("На уровне кварков:")
            print("p(uud) + p(uud) → p(uud) + n(udd) + π⁺(uđ)")
            print()
            print("Пошагово:")
            print("1. d-кварк из первого протона испускает виртуальный W⁺")
            print("2. W⁺ распадается на u-кварк и đ-антикварк (образуя π⁺)")
            print("3. u-кварк из π⁺ поглощается d-кварком второго протона")
            print("4. d-кварк превращается в u-кварк через слабое взаимодействие")
            print("5. Первый протон превращается в нейтрон (uud → udd)")
            print()
            print("Сохранение заряда: (+1) + (+1) = (+1) + (0) + (+1)")
            print("Сохранение барионного числа: 1 + 1 = 1 + 1 + 0")
        
        return process
    
    def calculate_cross_section(self, energy, process_key):
        """Упрощенный расчет сечения"""
        process = self.processes[process_key]
        
        if energy < process['min_energy']:
            return 0.0
        
        # Упрощенная модель: сечение растет, затем падает
        excess_energy = energy - process['min_energy']
        cs = process['cross_section'] * excess_energy * np.exp(-excess_energy/2)
        
        return max(cs, 0.0)
    
    def run_simulation(self):
        """Запуск симуляции адронных взаимодействий"""
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║             СИМУЛЯТОР АДРОННЫХ ВЗАИМОДЕЙСТВИЙ             ║")
        print("║           с кварковой структурой и диаграммами Фейнмана   ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        
        print("\nДоступные процессы:")
        for key, proc in self.processes.items():
            print(f"{key}: {proc['description']}")
        
        while True:
            print("\n" + "="*60)
            process_key = input("\nВыберите процесс [pp_pnpi]: ").strip() or "pp_pnpi"
            
            if process_key not in self.processes:
                print("❌ Неизвестный процесс!")
                continue
            
            energy = float(input("Энергия в системе ЦМ (ГэВ): ").strip() or "2.0")
            
            # Проверка сохранения
            conservation = self.check_conservation_laws(process_key)
            
            # Расчет сечения
            cross_section = self.calculate_cross_section(energy, process_key)
            
            process = self.processes[process_key]
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"⚛️  Процесс: {process['description']}")
            print(f"⚡ Энергия: {energy} ГэВ")
            
            if not all(conservation.values()):
                print("❌ Нарушены законы сохранения!")
                for law, ok in conservation.items():
                    print(f"  {law}: {'✓' if ok else '✗'}")
            else:
                print(f"✅ Все законы сохранения соблюдены")
            
            if cross_section > 0:
                print(f"📈 Сечение: {cross_section:.2f} мб")
                print(f"📈 Вероятность процесса: {(cross_section/100):.1%}")
                
                # Объяснение процесса
                self.explain_quark_process(process_key)
                
                # Рисуем диаграмму
                print("\n🖼️  Генерируем диаграммы Фейнмана...")
                self.diagram.draw_pp_scattering()
            else:
                print(f"❌ Энергии недостаточно для процесса")
                print(f"   Минимальная энергия: {process['min_energy']} ГэВ")
            
            cont = input("\n🔄 Моделировать другой процесс? (y/n): ").strip().lower()
            if cont != 'y':
                print("👋 До свидания!")
                break

# Запуск симулятора
if __name__ == "__main__":
    simulator = HadronInteractionSimulator()
    
    print("🎯 ДЕМОНСТРАЦИЯ АДРОННЫХ ВЗАИМОДЕЙСТВИЙ")
    print("="*50)
    
    # Демонстрация сохранения
    print("\n🔬 Проверка законов сохранения для p+p → p+n+π⁺:")
    conservation = simulator.check_conservation_laws('pp_pnpi')
    for law, ok in conservation.items():
        print(f"  {law}: {'СОХРАНЯЕТСЯ ✓' if ok else 'НАРУШАЕТСЯ ✗'}")
    
    # Запуск интерактивной симуляции
    simulator.run_simulation()