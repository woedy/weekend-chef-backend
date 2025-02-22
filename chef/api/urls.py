from django.urls import path

from clients.api.views import add_client, get_all_clients_view, get_client_details_view, edit_client, archive_client, \
    get_all_archived_clients_view, unarchive_client, delete_client, add_client_complaint, edit_client_complaint, \
    get_all_client_complaints_view, get_client_complaint_details_view, archive_client_complaint, \
    unarchive_client_complaint, delete_client_complaint, get_all_archived_client_complaints_view, \
    change_complaint_status

app_name = 'chef'

urlpatterns = [
    path('add-client/', add_client, name="add_client"),
]
