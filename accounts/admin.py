# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SimulationLog
from django.utils.html import format_html

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 
        'email', 
        'simulation_count', 
        'rating_score', 
        'is_staff',
        'date_joined'
    ]
    list_filter = [
        'is_staff', 
        'is_superuser', 
        'is_email_verified',
        'date_joined'
    ]
    search_fields = ['username', 'email']
    ordering = ['-rating_score']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Рейтинг', {
            'fields': ('simulation_count', 'rating_score', 'last_simulation_time')
        }),
        ('Дополнительно', {
            'fields': ('is_email_verified',)
        }),
    )
    
    readonly_fields = ['last_simulation_time']


@admin.register(SimulationLog)
class SimulationLogAdmin(admin.ModelAdmin):
    
    list_display = [
        'id',
        'user_link',  # ← Ссылка на пользователя
        'simulation_type_display',  # ← Красивое отображение
        'energy_display',  # ← С единицами измерения
        'duration_display',  # ← С единицами измерения
        'created_at'
    ]

    list_filter = ['simulation_type', 'created_at', 'user']
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'user', 'simulation_type', 'energy', 'duration', 'simulation_results']
    
    # Группировка полей
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'simulation_type', 'created_at')
        }),
        ('Параметры симуляции', {
            'fields': ('energy', 'duration')
        }),
        ('Результаты', {
            'fields': ('simulation_results',),
            'classes': ('collapse',)  # Сворачиваемый блок
        }),
    )
    
    # Ссылка на пользователя
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/accounts/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user__username'
    
    # Красивое отображение типа
    def simulation_type_display(self, obj):
        colors = {
            'proton_proton': '#4A90E2',
            'proton_neutron': '#48BB78',
            'quark_collision': '#ED8936',
            'electron_positron': '#9F7AEA',
            'heavy_ion': '#F56565',
        }
        color = colors.get(obj.simulation_type, '#718096')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">{}</span>',
            color,
            obj.get_simulation_type_display() if hasattr(obj, 'get_simulation_type_display') else obj.simulation_type
        )
    simulation_type_display.short_description = 'Тип симуляции'
    simulation_type_display.admin_order_field = 'simulation_type'
    
    # Энергия с единицами
    def energy_display(self, obj):
        if obj.energy:
            return f"{obj.energy} ТэВ"
        return "-"
    energy_display.short_description = 'Энергия'
    energy_display.admin_order_field = 'energy'
    
    # Длительность с единицами
    def duration_display(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            if minutes > 0:
                return f"{minutes} мин {seconds} сек"
            return f"{seconds} сек"
        return "-"
    duration_display.short_description = 'Длительность'
    duration_display.admin_order_field = 'duration'

"""@admin.register(SimulationLog)
class SimulationLogAdmin(admin.ModelAdmin):
    
    list_display = [
        'user', 
        'simulation_type', 
        'energy', 
        'duration',
        'created_at'
    ]

    list_filter = ['simulation_type', 'created_at']
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']"""