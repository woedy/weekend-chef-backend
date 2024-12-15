from django.contrib import admin

from chats.models import PrivateChatRoom, PrivateRoomChatMessage, PrivateRoomChatImage

admin.site.register(PrivateChatRoom)
admin.site.register(PrivateRoomChatMessage)
admin.site.register(PrivateRoomChatImage)
