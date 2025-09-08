from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    
    class Meta:
        model = UserProfile
        fields = (
            "id", "user", "username", "email", "display_name", 
            "avatar", "preferences", "created_at", "updated_at"
        )
