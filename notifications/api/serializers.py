from django.contrib.auth import get_user_model
from rest_framework import serializers

from notifications.models import Notification


class NotificationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"




class AllNotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"



