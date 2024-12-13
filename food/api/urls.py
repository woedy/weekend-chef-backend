from django.urls import path

from food.api.dish_views import add_dish, get_all_dishs_view
from food.api.food_category_views import add_food_category, archive_food_category, delete_food_category, edit_food_category, get_all_archived_food_categorys_view, get_all_food_categorys_view, unarchive_food_category

app_name = 'food'

urlpatterns = [
    path('add-food-category/', add_food_category, name="add_food_category"),
    path('edit-food-category/', edit_food_category, name="edit_food_category"),
    path('get-all-food-categories/', get_all_food_categorys_view, name="get_all_food_categorys_view"),
    path('archive-food-category/', archive_food_category, name="archive_food_category"),
    path('unarchive-food-category/', unarchive_food_category, name="unarchive_food_category"),
    path('get-all-archived-food-categories/', get_all_archived_food_categorys_view, name="get_all_archived_food_categorys_view"),
    path('delete-food-category/', delete_food_category, name="delete_food_category"),



    path('add-dish/', add_dish, name="add_dish"),
    path('get-all-dishes/', get_all_dishs_view, name="get_all_dishs_view"),

]
