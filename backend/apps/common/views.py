# apps/common/views.py
from __future__ import annotations

from django.utils.text import slugify
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AddressSerializer


class AddressValidateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"valid": True, "data": serializer.validated_data}, status=status.HTTP_200_OK)
        return Response({"valid": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SlugPreviewView(APIView):
    def post(self, request, *args, **kwargs):
        name = request.data.get("name", "")
        preview = slugify(name)[:220] if name else ""
        return Response({"slug": preview}, status=status.HTTP_200_OK)
