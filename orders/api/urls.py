from django.urls import path

from orders.api.custom_options_view import add_custom_option



app_name = 'orders'

urlpatterns = [
    path('add-custom-option/', add_custom_option, name='add_custom_option'),


]
