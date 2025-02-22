from django.contrib import admin

from clients.models import Client, ClientHomeLocation

admin.site.register(Client)
admin.site.register(ClientHomeLocation)
