from django.urls import path

from food.api.dish_gallery_views import add_dish_gallery, archive_dish_gallery, delete_dish_gallery, get_all_archived_dish_gallerys_view, get_all_dish_gallerys_view, unarchive_dish_gallery
from food.api.dish_views import add_dish, archive_dish, delete_dish, edit_dish_view, get_all_archived_dishs_view, get_all_dishs_view, get_dish_details_view, unarchive_dish
from food.api.food_category_views import add_food_category, archive_food_category, delete_food_category, edit_food_category, get_all_archived_food_categorys_view, get_all_food_categorys_view, unarchive_food_category
from food.api.ingredients_views import add_ingredient, archive_ingredient, delete_ingredient, edit_ingredient_view, get_all_ingredients_view, get_all_unarchived_ingredient_view, get_ingredient_details_view, unarchive_ingredient

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
    path('edit-dish/', edit_dish_view, name="edit_dish_view"),
    path('get-dish-details/', get_dish_details_view, name="get_dish_detail_view"),
    path('archive-dish/', archive_dish, name="archive_dish"),
    path('unarchive-dish/', unarchive_dish, name="unarchive_dish"),
    path('get-all-archived-dish/', get_all_archived_dishs_view, name="get_all_archived_dish_view"),
    path('delete-dish/', delete_dish, name="delete_dish"),



    path('add-ingredient/', add_ingredient, name="add_ingredient"),
    path('get-all-ingredients/', get_all_ingredients_view, name="get_all_ingredients_view"),
    path('edit-ingredient/', edit_ingredient_view, name="edit_ingredient_view"),
    path('get-ingredient-details/', get_ingredient_details_view, name="get_ingredient_details_view"),

    path('archive-ingredient/', archive_ingredient, name="archive_ingredient"),
    path('unarchive-ingredient/', unarchive_ingredient, name="unarchive_ingredient"),
    path('get-all-unarchived-ingredients/', get_all_unarchived_ingredient_view, name="get_all_unarchived_ingredient_view"),
    path('delete-ingredient/', delete_ingredient, name="delete_ingredient"),


    path('add-dish-gallery/', add_dish_gallery, name="add_dish_gallery"),
    path('get-all-dish-gallery/', get_all_dish_gallerys_view, name="get_all_gallery_view"),
    path('archive-dish-gallery/', archive_dish_gallery, name="archive_dish_gallery"),
    path('unarchive-dish-gallery/', unarchive_dish_gallery, name="unarchive_dish_gallery"),
    path('get-all-archived-dish-gallery/', get_all_archived_dish_gallerys_view, name="get_all_archived_dish_gallery_view"),
    path('delete-dish-gallery/', delete_dish_gallery, name="delete_dish_gallery"),



]
