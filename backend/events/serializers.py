from rest_framework import serializers
from .models import Event, Participant

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'venue', 'date', 'max_participants']

class ParticipantSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)  # nested event details
    class Meta:
        model = Participant
        fields = ['id', 'name', 'email', 'phone', 'event', 'otp_code', 'otp_verified', 'qr_code', 'checked_in']
