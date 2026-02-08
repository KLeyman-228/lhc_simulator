# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import SimulationLog

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        label="Подтвердите пароль"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Пароли не совпадают!"
            })
        return attrs
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Этот username уже занят")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Этот email уже зарегистрирован")
        return value.lower()
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    
    rank = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'simulation_count', 
            'rating_score',
            'last_simulation_time',
            'rank',
            'created_at'
        ]
        read_only_fields = [
            'simulation_count', 
            'rating_score', 
            'last_simulation_time'
        ]
    
    def get_rank(self, obj):
        return User.objects.filter(rating_score__gt=obj.rating_score).count() + 1


class LeaderboardSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'simulation_count', 
            'rating_score', 
            'created_at'
        ]


class SimulationLogSerializer(serializers.ModelSerializer):
    
    simulation_type_display = serializers.CharField(
        source='get_simulation_type_display', 
        read_only=True
    )
    user_name = serializers.CharField(
        source='user.username', 
        read_only=True
    )
    
    class Meta:
        model = SimulationLog
        fields = [
            'id',
            'simulation_type',
            'simulation_type_display',
            'energy',
            'duration',
            'created_at',
            'user_name'
        ]