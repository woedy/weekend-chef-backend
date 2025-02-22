

from django.contrib.auth import get_user_model
from rest_framework import serializers

from chef.models import ChefProfile
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















class AllClosestChefSerializer(serializers.ModelSerializer):
    chef_full_name = serializers.SerializerMethodField()
    chef_photo = serializers.SerializerMethodField()

    

    class Meta:
        model = ChefProfile
        fields = ["chef_id", "chef_full_name","chef_photo", "kitchen_location", "lat", "lng"]


    def get_chef_full_name(self, obj):
        return (obj.user.first_name + " " + obj.user.last_name) if obj.user else None

    def get_chef_photo(self, obj):
        return (obj.user.photo.url) if obj.user.photo else None
