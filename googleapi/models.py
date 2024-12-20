from rest_framework import serializers

class AddressSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=255)
    destination = serializers.CharField(max_length=255)
