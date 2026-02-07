# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SimulationLog


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
        'user', 
        'simulation_type', 
        'energy', 
        'duration',
        'created_at'
    ]

    list_filter = ['simulation_type', 'created_at']
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']