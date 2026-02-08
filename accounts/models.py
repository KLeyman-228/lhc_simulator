from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email")
    is_email_verified = models.BooleanField(default=False)

    simulation_count = models.IntegerField(default=0)
    rating_score = models.IntegerField(default=0, verbose_name="Рейтинг")
    last_simulation_time = models.DateTimeField(null=True, blank=True, verbose_name="Последняя симуляция")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    #USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['-rating_score']
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        indexes = [
            models.Index(fields=['-rating_score']),
            models.Index(fields=['-simulation_count']),
        ]

    def __str__(self):
        return self.username

class SimulationLog(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='simulation',
        verbose_name="Пользователь"
    )

    simulation_type = models.CharField(
        max_length=50,
        verbose_name="Тип симуляции"
    )

    energy = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="Энергия (ТэВ)"
    )

    duration = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Длительность (сек)"
    )

    simulation_results = models.JSONField(
        default=list, 
        blank=True,
        verbose_name="Результаты столкновения",
        help_text="Список обнаруженных частиц и событий"
    )

    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата запуска"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Запуск симуляции"
        verbose_name_plural = "Запуски симуляций"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.simulation_type} ({self.created_at.strftime('%d.%m.%Y')})"
        # Убрали get_simulation_type_display() ↑