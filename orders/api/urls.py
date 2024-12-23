from django.urls import path

from orders.api.cart_views import add_cart_item, cart_item_detail_view, edit_cart_item_view, get_all_carts_view, get_cart_detail_view
from orders.api.custom_options_view import add_custom_option, archive_custom_option, delete_custom_option, edit_custom_option_view, get_all_archived_custom_options_view, get_all_custom_options_view, get_custom_option_details_view, unarchive_custom_option
from orders.api.orders import place_order_view



app_name = 'orders'

urlpatterns = [
    path('add-custom-option/', add_custom_option, name='add_custom_option'),
    path('get-all-custom-option/', get_all_custom_options_view, name='get_all_custom_options_view'),
    path('edit-custom-option/', edit_custom_option_view, name="edit_custom_option_view"),
    path('get-custom-option-details/', get_custom_option_details_view, name="get_custom_option_detail_view"),
    path('archive-custom-option/', archive_custom_option, name="archive_custom_option"),
    path('unarchive-custom-option/', unarchive_custom_option, name="unarchive_custom_option"),
    path('get-all-archived-custom-option/', get_all_archived_custom_options_view, name="get_all_archived_custom_option_view"),
    path('delete-custom-option/', delete_custom_option, name="delete_custom_option"),



path('add-cart-item/', add_cart_item, name='add_cart_item'),
path('get-all-cart-items/', get_all_carts_view, name='get_all_carts_view'),
    path('edit-cart-item/', edit_cart_item_view, name="edit_cart_item_view"),
    path('get-cart-item-details/', cart_item_detail_view, name="cart_item_detail_view"),

path('place-order/', place_order_view, name='place_order_view'),

]
