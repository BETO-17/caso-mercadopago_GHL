# payments/serializers.py
from rest_framework import serializers
from .models import PaymentPreference

class CreatePaymentSerializer(serializers.Serializer):
    appointmentId = serializers.CharField()
    contactId = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField()

class PaymentPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPreference
        fields = '__all__'
