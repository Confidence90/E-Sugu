from rest_framework import serializers
from .models import LiveStream

class LiveStreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveStream
        fields = '__all__'