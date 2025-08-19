from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *


class UserSerializer(serializers.ModelSerializer):
    tokens = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True, default=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'is_active', 'tokens', 'allow_networking', 'followers_count', 'following_count']
        read_only_fields = ['is_active', 'followers_count', 'following_count']

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def create(self, validated_data):
        validated_data['is_active'] = True
        user = User.objects.create_user(**validated_data)
        return user


class ChecklistSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()  # Use custom method for better control
    
    class Meta:
        model = Checklist
        fields = '__all__'
    
    def get_score(self, obj):
        """Custom score handling to preserve decimal precision"""
        try:
            # Convert to float and preserve precision
            score_value = float(obj.score)
            print(f"DEBUG: Checklist {obj.id} - DB score: {obj.score}, Type: {type(obj.score)}, Converted: {score_value}")
            return score_value
        except Exception as e:
            print(f"DEBUG: Error converting score for checklist {obj.id}: {e}")
            return 1.0  # Fallback


class RegretSerializer(serializers.ModelSerializer):
    checklist = serializers.HiddenField(default=None)

    class Meta:
        model = Regret
        fields = '__all__'


class NetworkSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)
    
    class Meta:
        model = Network
        fields = ['id', 'follower', 'follower_username', 'following', 'following_username', 'created_at']
        read_only_fields = ['follower_username', 'following_username', 'created_at']


class NetworkUserSerializer(serializers.ModelSerializer):
    regret_index = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'regret_index', 'followers_count', 'following_count', 'date_joined']
    
    def get_regret_index(self, obj):
        """Get regret index for today"""
        return obj.get_regret_index()
