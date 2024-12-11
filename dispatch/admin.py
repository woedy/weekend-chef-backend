from django.contrib import admin

from clients.models import Client, ClientContact, ClientGuardFile, ClientNote, ClientComplaint

admin.site.register(Client)
admin.site.register(ClientContact)
admin.site.register(ClientGuardFile)
admin.site.register(ClientNote)
admin.site.register(ClientComplaint)
