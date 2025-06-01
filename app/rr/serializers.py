from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *


class UserSerializer(serializers.ModelSerializer):
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'is_active', 'tokens']

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = '__all__'


class RegretSerializer(serializers.ModelSerializer):
    checklist = serializers.HiddenField(default=None)

    class Meta:
        model = Regret
        fields = '__all__'
