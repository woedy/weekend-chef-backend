

from django.contrib.auth import get_user_model
from rest_framework import serializers

from orders.models import CustomizationOption


User = get_user_model()



class AllCustomizationOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomizationOption
        fields = "__all__"


class CustomizationOptionDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomizationOption
        fields = "__all__"