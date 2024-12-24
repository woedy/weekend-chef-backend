import math
import random
import re
import string
from django.contrib.auth import get_user_model, authenticate




def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def generate_random_otp_code():
    code = ''
    for i in range(4):
        code += str(random.randint(0, 9))
    return code


def unique_user_id_generator(instance):
    """
    This is for a django project with a user_id field
    :param instance:
    :return:
    """

    size = random.randint(30,45)
    user_id = random_string_generator(size=size)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(user_id=user_id).exists()
    if qs_exists:
        return
    return user_id





def unique_chef_id_generator(instance):
    """
    This is for a chef_id field
    :param instance:
    :return:H
    """
    size = random.randint(5, 10)
    chef_id = "CH-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-F"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(chef_id=chef_id).exists()
    if qs_exists:
        return None
    return chef_id

def generate_email_token():
    code = ''
    for i in range(4):
        code += str(random.randint(0, 9))
    return code




def unique_client_id_generator(instance):
    """
    This is for a client_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 10)
    client_id = "CL-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-NT"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(client_id=client_id).exists()
    if qs_exists:
        return None
    return client_id


def unique_dispatch_id_generator(instance):
    """
    This is for a dispatch_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 10)
    dispatch_id = "DIS-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-CT"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(dispatch_id=dispatch_id).exists()
    if qs_exists:
        return None
    return dispatch_id




def unique_admin_id_generator(instance):
    """
    This is for a admin_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 10)
    admin_id = "AD-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-IN"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(admin_id=admin_id).exists()
    if qs_exists:
        return None
    return admin_id



def unique_dish_id_generator(instance):
    """
    This is for a dish_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 10)
    dish_id = "DI-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-SH"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(dish_id=dish_id).exists()
    if qs_exists:
        return None
    return dish_id

def unique_ingredient_id_generator(instance):
    """
    This is for a ingredient_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 10)
    ingredient_id = "ING-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-NT"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(ingredient_id=ingredient_id).exists()
    if qs_exists:
        return None
    return ingredient_id

def unique_order_id_generator(instance):
    """
    This is for a order_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 10)
    order_id = "ORD-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-ER"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(order_id=order_id).exists()
    if qs_exists:
        return None
    return order_id

def unique_custom_option_id_generator(instance):
    """
    This is for a custom_option_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 10)
    custom_option_id = "CO-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-O"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(custom_option_id=custom_option_id).exists()
    if qs_exists:
        return None
    return custom_option_id

def unique_dish_gallery_id_generator(instance):
    """
    This is for a ingredient_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 10)
    dish_gallery_id = "DG-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-D"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(dish_gallery_id=dish_gallery_id).exists()
    if qs_exists:
        return None
    return dish_gallery_id


def unique_booking_id_generator(instance):
    """
    This is for a booking_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 7)
    booking_id = "BK-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "_AP"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(booking_id=booking_id).exists()
    if qs_exists:
        return None
    return booking_id

def unique_room_id_generator(instance):
    """
    This is for a room_id field
    :param instance:
    :return:
    """
    size = random.randint(30, 45)
    room_id = random_string_generator(size=size)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(room_id=room_id).exists()
    if qs_exists:
        return None
    return room_id




def unique_account_id_generator(instance):
    """
    This is for a account_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 7)
    account_id = "ACC-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-(BNK)"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(account_id=account_id).exists()
    if qs_exists:
        return None
    return account_id


def unique_transaction_id_generator(instance):
    """
    This is for a transaction_id field
    :param instance:
    :return:
    """
    size = random.randint(5, 7)
    transaction_id = "TRN-" + random_string_generator(size=size, chars=string.ascii_uppercase + string.digits) + "-(P)"

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(transaction_id=transaction_id).exists()
    if qs_exists:
        return None
    return transaction_id



def haversine(lon1, lat1, lon2, lat2):
    # Check for None values
    if None in (lon1, lat1, lon2, lat2):
        raise ValueError("Coordinates cannot be None.")

    R = 6371  # Earth radius in kilometers

    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))

    return R * c  # Distance in kilometers




    
def convert_phone_number(phone):
    # Match pattern for phone numbers starting with "+" followed by the country code
    # and replace with "0" + the local part of the number.
    match = re.match(r"^\+(\d{1,3})(\d{9,10})$", phone)
    if match:
        return "0" + match.group(2)  # Extracts the local number part and prepends "0"
    return phone
