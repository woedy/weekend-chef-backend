from django.urls import path

from payments.api.views import get_transactions



app_name = 'orders'

urlpatterns = [
    path('transactions/', get_transactions, name='get_transactions'),


]
