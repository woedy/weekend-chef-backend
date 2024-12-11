from django.contrib.auth import get_user_model
from rest_framework import serializers

from clients.models import Client, ClientComplaint

User = get_user_model()


class ClientUserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "__all__"

class AllClientsUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "__all__"


class ClientDetailsSerializer(serializers.ModelSerializer):
    user = ClientUserDetailSerializer(many=False)
    class Meta:
        model = Client
        fields = "__all__"


class AllClientsSerializer(serializers.ModelSerializer):
    user = AllClientsUserSerializer(many=False)
    class Meta:
        model = Client
        fields = "__all__"




class ClientComplaintDetailSerializer(serializers.ModelSerializer):
    client = ClientDetailsSerializer(many=False)

    class Meta:
        model = ClientComplaint
        fields = "__all__"

class AllClientComplaintsSerializer(serializers.ModelSerializer):
    client = ClientDetailsSerializer(many=False)
    class Meta:
        model = ClientComplaint
        fields = "__all__"
