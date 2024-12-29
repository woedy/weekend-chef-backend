from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.api.custom_jwt import CustomJWTAuthentication
from notifications.api.serializers import AllNotificationsSerializer
from notifications.models import Notification


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def set_notification_to_read(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        notification_id = request.data.get('notification_id', "")


        if not notification_id:
            errors['notification_id'] = ['Notification ID is required.']



        try:
            notification = Notification.objects.get(id=notification_id)
        except:
            errors['notification_id'] = ['Notification does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        notification.read = True
        notification.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)







@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def get_all_notifications(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    filter_department = request.query_params.get('filter_department', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    all_notification = Notification.objects.all().order_by('-created_at')


    if search_query:
        all_notification = all_notification.filter(
            Q(department__icontains=search_query)
        )

    if filter_department:
        all_notification = all_notification.filter(
            department__icontains=filter_department
        )


    paginator = Paginator(all_notification, page_size)

    try:
        paginated_notification = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_notification = paginator.page(1)
    except EmptyPage:
        paginated_notification = paginator.page(paginator.num_pages)

    all_notifications_serializer = AllNotificationsSerializer(paginated_notification, many=True)


    data['notifications'] = all_notifications_serializer.data
    data['pagination'] = {
        'page_number': paginated_notification.number,
        'total_pages': paginator.num_pages,
        'next': paginated_notification.next_page_number() if paginated_notification.has_next() else None,
        'previous': paginated_notification.previous_page_number() if paginated_notification.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def delete_notification(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        notification_id = request.data.get('notification_id', "")

        if not notification_id:
            errors['notification_id'] = ['Notification ID is required.']

        try:
            notification = Notification.objects.get(id=notification_id)
        except:
            errors['notification_id'] = ['Notification does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        notification.delete()


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


