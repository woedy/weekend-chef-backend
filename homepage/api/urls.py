from django.urls import path

from homepage.api.views import get_homepage_data_view

app_name = 'homepage'

urlpatterns = [
    path('client-homepage-data/', get_homepage_data_view, name="get_homepage_data_view")
]
