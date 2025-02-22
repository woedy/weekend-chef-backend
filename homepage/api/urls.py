from django.urls import path

from homepage.api.views import get_admin_dashboard_data_view, get_chef_homepage_data_view, get_homepage_data_view

app_name = 'homepage'

urlpatterns = [
    path('client-homepage-data/', get_homepage_data_view, name="get_homepage_data_view"),
    path('admin-dashboard-data/', get_admin_dashboard_data_view, name="get_admin_dashboard_data_view"),

    path('chef-homepage-data/', get_chef_homepage_data_view, name="get_chef_homepage_data_view"),

]
