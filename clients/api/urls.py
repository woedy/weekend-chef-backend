from django.urls import path

from clients.api.client_dish_views import get_all_client_food_categories, get_all_client_food_sub_categories, get_client_dish_details_view
from clients.api.views import add_client, get_all_clients_view, get_client_details_view, edit_client, archive_client, \
    get_all_archived_clients_view, unarchive_client, delete_client, add_client_complaint, edit_client_complaint, \
    get_all_client_complaints_view, get_client_complaint_details_view, archive_client_complaint, \
    unarchive_client_complaint, delete_client_complaint, get_all_archived_client_complaints_view, \
    change_complaint_status

app_name = 'clients'

urlpatterns = [
    path('add-client/', add_client, name="add_client"),
    path('edit-client/', edit_client, name="edit_client"),
    path('get-all-clients/', get_all_clients_view, name="get_all_clients_view"),
    path('get-client-details/', get_client_details_view, name="get_client_details_view"),
    path('archive-client/', archive_client, name="archive_client"),
    path('delete-client/', delete_client, name="delete_client"),
    path('unarchive-client/', unarchive_client, name="unarchive_client"),
    path('get-all-archived-clients/', get_all_archived_clients_view, name="get_all_archived_clients_view"),

    path('add-client-complaint/', add_client_complaint, name="add_client_complaint"),
    path('edit-client-complaint/', edit_client_complaint, name="edit_client_complaint"),
    path('get-all-client-complaints/', get_all_client_complaints_view, name="get_all_client_complaints_view"),
    path('get-client-complaint-details/', get_client_complaint_details_view, name="get_client_complaint_details_view"),
    path('archive-client-complaint/', archive_client_complaint, name="archive_client_complaint"),
    path('unarchive-client-complaint/', unarchive_client_complaint, name="unarchive_client_complaint"),
    path('delete-client-complaint/', delete_client_complaint, name="delete_client_complaint"),
    path('get-all-archived-client-complaints/', get_all_archived_client_complaints_view, name="get_all_archived_client_complaints_view"),

    path('change-complaint-status/', change_complaint_status, name="change_complaint_status"),


path('get-client-dish-details/', get_client_dish_details_view, name="get_client_dish_details_view"),
path('get-all-client-food-categories/', get_all_client_food_categories, name="get_all_client_food_categories"),
path('get-all-client-food-sub-categories/', get_all_client_food_sub_categories, name="get_all_client_food_sub_categories"),


]
