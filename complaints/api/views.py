
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.api.custom_jwt import CustomJWTAuthentication
from accounts.api.client_views import is_valid_email, check_email_exist
from activities.models import AllActivity
from clients.api.serializers import AllClientsSerializer, ClientDetailsSerializer, AllClientComplaintsSerializer, \
    ClientComplaintDetailSerializer

from clients.models import Client, ClientComplaint

User = get_user_model()




@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def add_client_complaint(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        client_id = request.data.get('client_id', "")
        representative = request.data.get('representative', "")
        title = request.data.get('title', "")
        note = request.data.get('note', "")

        if not client_id:
            errors['client_id'] = ['Client ID is required.']

        if not title:
            errors['title'] = ['Title is required.']

        if not note:
            errors['note'] = ['Note is required.']
        if not representative:
            errors['representative'] = ['Representative is required.']


        try:
            client = Client.objects.get(client_id=client_id)
        except:
            errors['client_id'] = ['Client does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        new_complaint = ClientComplaint.objects.create(
            client=client,
            representative=representative,
            title=title,
            note=note,

        )

        data["complaint_id"] = new_complaint.complaint_id

        new_activity = AllActivity.objects.create(
            user=client.user,
            subject="New Client Complaint",
            body=client.user.email + " Added a new complaint."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def edit_client_complaint(request):
    payload = {}
    data = {}
    errors = {}


    if request.method == 'POST':
        complaint_id = request.data.get('complaint_id', "")
        representative = request.data.get('representative', "")
        client_id = request.data.get('client_id', "")
        title = request.data.get('title', "")
        note = request.data.get('note', "")

        if not client_id:
            errors['client_id'] = ['Client ID is required.']

        if not title:
            errors['title'] = ['Title is required.']

        if not note:
            errors['note'] = ['Note is required.']


        try:
            client = Client.objects.get(client_id=client_id)
        except:
            errors['client_id'] = ['Client does not exist.']

        try:
            complaint = ClientComplaint.objects.get(complaint_id=complaint_id)
        except:
            errors['complaint_id'] = ['Complaint does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        complaint.client = client
        complaint.representative = representative
        complaint.title = title
        complaint.representative = representative
        complaint.note = note
        complaint.save()


        data["complaint_id"] = complaint_id

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def change_complaint_status(request):
    payload = {}
    data = {}
    errors = {}


    if request.method == 'POST':
        complaint_id = request.data.get('complaint_id', "")
        status = request.data.get('status', "")

        if not status:
            errors['status'] = ['Status is required.']


        try:
            complaint = ClientComplaint.objects.get(complaint_id=complaint_id)
        except:
            errors['complaint_id'] = ['Complaint does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        complaint.status = status
        complaint.save()


        data["complaint_id"] = complaint_id

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def get_all_client_complaints_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    all_client_complaints = ClientComplaint.objects.all().filter(is_archived=False)


    if search_query:
        all_client_complaints = all_client_complaints.filter(
            Q(client_client_id__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(note__icontains=search_query)
        )


    paginator = Paginator(all_client_complaints, page_size)

    try:
        paginated_client_complaints = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_client_complaints = paginator.page(1)
    except EmptyPage:
        paginated_client_complaints = paginator.page(paginator.num_pages)

    all_client_complaints_serializer = AllClientComplaintsSerializer(paginated_client_complaints, many=True)


    data['complaints'] = all_client_complaints_serializer.data
    data['pagination'] = {
        'page_number': paginated_client_complaints.number,
        'total_pages': paginator.num_pages,
        'next': paginated_client_complaints.next_page_number() if paginated_client_complaints.has_next() else None,
        'previous': paginated_client_complaints.previous_page_number() if paginated_client_complaints.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def get_client_complaint_details_view(request):
    payload = {}
    data = {}
    errors = {}

    complaint_id = request.query_params.get('complaint_id', None)

    if not complaint_id:
        errors['complaint_id'] = ["Complaint ID required"]

    try:
        complaint = ClientComplaint.objects.get(complaint_id=complaint_id)
    except Client.DoesNotExist:
        errors['complaint_id'] = ['Complaint does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    complaint_serializer = ClientComplaintDetailSerializer(complaint, many=False)
    if complaint_serializer:
        complaint = complaint_serializer.data


    payload['message'] = "Successful"
    payload['data'] = complaint

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def archive_client_complaint(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        complaint_id = request.data.get('complaint_id', "")

        if not complaint_id:
            errors['complaint_id'] = ['Complaint ID is required.']

        try:
            complaint = ClientComplaint.objects.get(complaint_id=complaint_id)
        except:
            errors['complaint_id'] = ['Complaint does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        complaint.is_archived = True
        complaint.save()



        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def unarchive_client_complaint(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        complaint_id = request.data.get('complaint_id', "")

        if not complaint_id:
            errors['complaint_id'] = ['Complaint ID is required.']

        try:
            complaint = ClientComplaint.objects.get(complaint_id=complaint_id)
        except:
            errors['complaint_id'] = ['Complaint does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        complaint.is_archived = False
        complaint.save()



        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def delete_client_complaint(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        complaint_id = request.data.get('complaint_id', "")

        if not complaint_id:
            errors['complaint_id'] = ['Complaint ID is required.']

        try:
            complaint = ClientComplaint.objects.get(complaint_id=complaint_id)
        except:
            errors['complaint_id'] = ['Complaint does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        complaint.delete()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def get_all_archived_client_complaints_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    all_client_complaints = ClientComplaint.objects.all().filter(is_archived=True)


    if search_query:
        all_client_complaints = all_client_complaints.filter(
            Q(client_client_id__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(note__icontains=search_query)
        )


    paginator = Paginator(all_client_complaints, page_size)

    try:
        paginated_client_complaints = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_client_complaints = paginator.page(1)
    except EmptyPage:
        paginated_client_complaints = paginator.page(paginator.num_pages)

    all_client_complaints_serializer = AllClientComplaintsSerializer(paginated_client_complaints, many=True)


    data['complaints'] = all_client_complaints_serializer.data
    data['pagination'] = {
        'page_number': paginated_client_complaints.number,
        'total_pages': paginator.num_pages,
        'next': paginated_client_complaints.next_page_number() if paginated_client_complaints.has_next() else None,
        'previous': paginated_client_complaints.previous_page_number() if paginated_client_complaints.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)

