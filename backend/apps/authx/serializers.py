from __future__ import annotations

from typing import Any, Dict

from rest_framework import serializers

from .models import UserProfile


class ConsentUpdateSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=64)
    granted = serializers.BooleanField()
    source = serializers.CharField(max_length=64, required=False, allow_blank=True, default="api")


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    # Écriture de consents via un champ spécifique (liste d’updates)
    consent_updates = ConsentUpdateSerializer(many=True, write_only=True, required=False)

    # Expose un snapshot compact des consents
    consents_snapshot = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        # ⚠️ On ne permet pas d’écrire 'user' depuis l’API
        fields = (
            "id",
            "username",
            "email",
            "display_name",
            "avatar",
            "preferences",
            "consents",           # lecture seule brute
            "consents_snapshot",  # lecture compacte
            "consent_updates",    # écriture
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "consents")

    def get_consents_snapshot(self, obj: UserProfile) -> Dict[str, Any]:
        return obj.last_consents_snapshot()

    def validate_preferences(self, value):
        # Taille max validée en modèle aussi, mais on double-check côté serializer
        import json
        from django.conf import settings
        max_bytes = getattr(settings, "AUTHX_PREFERENCES_MAX_BYTES", 32 * 1024)
        try:
            raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        except Exception as exc:
            raise serializers.ValidationError(f"Invalid JSON: {exc}")
        if len(raw) > max_bytes:
            raise serializers.ValidationError(f"Size exceeds {max_bytes} bytes")
        return value

    def update(self, instance: UserProfile, validated_data):
        updates = validated_data.pop("consent_updates", None)
        # Champs simples
        instance.display_name = validated_data.get("display_name", instance.display_name)
        instance.avatar = validated_data.get("avatar", instance.avatar)
        if "preferences" in validated_data:
            instance.preferences = validated_data["preferences"]

        # Consents
        if updates:
            for upd in updates:
                instance.set_consent(upd["key"], upd["granted"], upd.get("source") or "api")

        instance.full_clean()
        instance.save()
        return instance
