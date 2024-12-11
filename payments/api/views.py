import re
from decimal import Decimal

from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import requests

from slots.models import StaffSlot, TimeSlot
from django.db.models import Q
from django.conf import settings

User = get_user_model()

@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def shop_bookings_view(request):
    payload = {}
    data = {}
    errors = {}

    shop_id = request.query_params.get('shop_id', None)
    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)

    _status = request.query_params.get('status', '')
    date = request.query_params.get('date', '')
    page_size = 10

    if not shop_id:
        errors['shop_id'] = ['Shop ID is required.']

    try:
        shop = Shop.objects.get(shop_id=shop_id)
    except Shop.DoesNotExist:
        errors['shop_id'] = ['Shop does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)



    bookings = Booking.objects.filter(shop=shop).order_by('-created_at')

    if search_query:
        bookings = bookings.filter(
            Q(booking_id__icontains=search_query)|
            Q(client__full_name__icontains=search_query) |
            Q(client__full_name__icontains=search_query)
            )
        
    
        

        
    if _status:
        bookings = bookings.filter(status=_status)

    if date:
        bookings = bookings.filter(booking_date=date)

    paginator = Paginator(bookings, page_size)

    try:
        paginated_bookings = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_bookings = paginator.page(1)
    except EmptyPage:
        paginated_bookings = paginator.page(paginator.num_pages)

    booking_serializer = ListBookingSerializer(paginated_bookings, many=True)

    data['bookings'] = booking_serializer.data
    data['pagination'] = {
        'page_number': paginated_bookings.number,
        'total_pages': paginator.num_pages,
        'next': paginated_bookings.next_page_number() if paginated_bookings.has_next() else None,
        'previous': paginated_bookings.previous_page_number() if paginated_bookings.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_transactions(request):

    payload = {}
    data = {}
    errors = {}

    url = "https://api.paystack.co/transaction"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        transactions = response.json()
        data['transactions'] = transactions
    else:
        errors['transactions'] = ['Failed to load transactions']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)

