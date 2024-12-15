from rest_framework import serializers
from django.contrib.auth import get_user_model

from chats.models import PrivateRoomChatMessage, PrivateChatRoom
from shop.models import Shop
from user_profile.models import UserProfile

User = get_user_model()

class UserPersonalInfoRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'photo',
            'phone',
        ]

class UserRoomSerializer(serializers.ModelSerializer):
    personal_info = UserPersonalInfoRoomSerializer(many=False)
    class Meta:
        model = User
        fields = [
            'user_id',
            'email',
            'full_name',
            'personal_info'
        ]

class ShopRoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = [
            'shop_id',
            'shop_name',
            'photo'
        ]

class ShopUserRoomSerializer(serializers.ModelSerializer):
    shop_user = ShopRoomSerializer(many=False)
    class Meta:
        model = User
        fields = [
            'user_id',
            'email',
            'full_name',
            'shop_user'
        ]


class PrivateRoomSerializer(serializers.ModelSerializer):
    shop = ShopUserRoomSerializer(many=False)
    client = UserRoomSerializer(many=False)

    class Meta:
        model = PrivateChatRoom
        fields = [
            'room_id',
            'shop',
            'client',
        ]

class PrivateRoomChatMessageSerializer(serializers.ModelSerializer):
    room = PrivateRoomSerializer(many=False)
    sender = serializers.SerializerMethodField()

    class Meta:
        model = PrivateRoomChatMessage
        fields = ['id','room', 'message', 'timestamp', 'read', 'sender' ]

    def get_sender(self, obj):
        sender_id = obj.user.user_id
        return sender_id



