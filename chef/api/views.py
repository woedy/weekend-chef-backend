
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
@authentication_classes([TokenAuthentication, ])
def add_client(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        email = request.data.get('email', "").lower()
        company_name = request.data.get('company_name', "")
        first_name = request.data.get('first_name', "")
        last_name = request.data.get('last_name', "")
        phone = request.data.get('phone', "")
        purpose = request.data.get('purpose', "")
        photo = request.data.get('photo', "")
        person_in_charge = request.data.get('person_in_charge', "")
        client_type = request.data.get('client_type', "")

        if not email:
            errors['email'] = ['User Email is required.']
        elif not is_valid_email(email):
            errors['email'] = ['Valid email required.']
        elif check_email_exist(email):
            errors['email'] = ['Email already exists in our database.']

        if not company_name:
            errors['company_name'] = ['Company Name is required.']

        if not first_name:
            errors['first_name'] = ['First Name is required.']

        if not phone:
            errors['phone'] = ['Phone number is required.']

        if not last_name:
            errors['last_name'] = ['Last Name is required.']

        if not purpose:
            errors['purpose'] = ['Purpose is required.']

        if not client_type:
            errors['client_type'] = ['Client Type is required.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            department="CLIENT",
            photo=photo
        )

        client_profile = Client.objects.create(
            user=user,
            purpose=purpose,
            company_name=company_name,
            person_in_charge=person_in_charge,
            client_type=client_type,

        )

        data["user_id"] = user.user_id
        data["client_id"] = client_profile.client_id
        data["company_name"] = client_profile.company_name
        data["purpose"] = client_profile.purpose
        data["email"] = user.email
        data["first_name"] = user.first_name
        data["last_name"] = user.last_name


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def get_all_clients_view222(request):
    payload = {}
    data = {}
    errors = {}

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    all_clients = Client.objects.all().filter(user__is_archived=False)

    all_clients_serializer = AllClientsSerializer(all_clients, many=True)
    if all_clients_serializer:
        _all_clients = all_clients_serializer.data

    payload['message'] = "Successful"
    payload['data'] = _all_clients


    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def get_all_clients_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    all_clients = Client.objects.all().filter(user__is_archived=False)


    if search_query:
        all_clients = all_clients.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__department__icontains=search_query) |
            Q(user__gender__icontains=search_query) |
            Q(user__dob__icontains=search_query) |
            Q(user__marital_status__icontains=search_query) |
            Q(user__phone__icontains=search_query) |
            Q(user__country__icontains=search_query) |
            Q(user__language__icontains=search_query) |
            Q(user__location_name__icontains=search_query)
        )


    paginator = Paginator(all_clients, page_size)

    try:
        paginated_clients = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_clients = paginator.page(1)
    except EmptyPage:
        paginated_clients = paginator.page(paginator.num_pages)

    all_clients_serializer = AllClientsSerializer(paginated_clients, many=True)


    data['clients'] = all_clients_serializer.data
    data['pagination'] = {
        'page_number': paginated_clients.number,
        'total_pages': paginator.num_pages,
        'next': paginated_clients.next_page_number() if paginated_clients.has_next() else None,
        'previous': paginated_clients.previous_page_number() if paginated_clients.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def get_client_details_view(request):
    payload = {}
    data = {}
    errors = {}

    client_id = request.query_params.get('client_id', None)

    if not client_id:
        errors['client_id'] = ["Client id required"]

    try:
        client = Client.objects.get(client_id=client_id)
    except Client.DoesNotExist:
        errors['client_id'] = ['Client does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    client_serializer = ClientDetailsSerializer(client, many=False)
    if client_serializer:
        client = client_serializer.data

    client_serializer = ClientDetailsSerializer(client, many=False)

    payload['message'] = "Successful"
    payload['data'] = client

    return Response(payload, status=status.HTTP_200_OK)

@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def edit_client(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        client_id = request.data.get('client_id', "")
        email = request.data.get('email', "").lower()
        company_name = request.data.get('company_name', "")
        first_name = request.data.get('first_name', "")
        last_name = request.data.get('last_name', "")
        phone = request.data.get('phone', "")
        purpose = request.data.get('purpose', "")
        gender = request.data.get('gender', "")
        person_in_charge = request.data.get('person_in_charge', "")
        client_type = request.data.get('client_type', "")



        legal_Form = request.data.get('legal_Form', "")
        share_capital = request.data.get('share_capital', "")
        registration_number = request.data.get('registration_number', "")
        title_of_person = request.data.get('title_of_person', "")
        type_of_work = request.data.get('type_of_work', "")
        address = request.data.get('address', "")
        passport_id_number = request.data.get('passport_id_number', "")



        if not client_id:
            errors['client_id'] = ['Client ID is required.']

        if not email:
            errors['email'] = ['User Email is required.']
        elif not is_valid_email(email):
            errors['email'] = ['Valid email required.']

        if not company_name:
            errors['company_name'] = ['Company Name is required.']

        if not first_name:
            errors['first_name'] = ['First Name is required.']

        if not phone:
            errors['phone'] = ['Phone number is required.']

        if not last_name:
            errors['last_name'] = ['Last Name is required.']

        if not purpose:
            errors['purpose'] = ['Purpose is required.']

        if not client_type:
            errors['client_type'] = ['Client Type is required.']

        try:
            client_profile = Client.objects.get(client_id=client_id)
        except Client.DoesNotExist:
            errors['client_id'] = ['Client does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Update fields only if provided and not empty
        if first_name:
            client_profile.user.first_name = first_name
        if last_name:
            client_profile.user.last_name = last_name
        if phone:
            client_profile.user.phone = phone
        if email:
            client_profile.user.email = email

        if gender:
            client_profile.user.gender = gender
        client_profile.user.save()


        if purpose:
            client_profile.purpose = purpose
        if person_in_charge:
            client_profile.person_in_charge = person_in_charge
        if client_type:
            client_profile.client_type = client_type


        if legal_Form:
            client_profile.legal_Form = legal_Form


        if share_capital:
            client_profile.share_capital = share_capital

        if registration_number:
            client_profile.registration_number = registration_number


        if title_of_person:
            client_profile.title_of_person = title_of_person


        if type_of_work:
            client_profile.type_of_work = type_of_work
        
        if address:
            client_profile.address = address

        
        if passport_id_number:
            client_profile.passport_id_number = passport_id_number


        client_profile.save()

        data["user_id"] = client_profile.user.user_id
        data["email"] = client_profile.user.email
        data["company_name"] = client_profile.company_name
        data["first_name"] = client_profile.user.first_name
        data["last_name"] = client_profile.user.last_name
        data["purpose"] = client_profile.purpose
        data["gender"] = client_profile.user.gender

        new_activity = AllActivity.objects.create(
            user=client_profile.user,
            subject="Profile Edited",
            body=f"{client_profile.user.email} just edited their account."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def archive_client(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        client_id = request.data.get('client_id', "")

        if not client_id:
            errors['client_id'] = ['Client ID is required.']

        try:
            client = Client.objects.get(client_id=client_id)
        except:
            errors['client_id'] = ['Client does not exist.']

        try:
            user = User.objects.get(user_id=client.user.user_id)
        except:
            errors['user_id'] = ['User does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        user.is_archived = True
        user.save()

        new_activity = AllActivity.objects.create(
            user=user,
            subject="Account Archived",
            body=user.email + " account archived."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def delete_client(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        client_id = request.data.get('client_id', "")

        if not client_id:
            errors['client_id'] = ['Client ID is required.']

        try:
            client = Client.objects.get(client_id=client_id)
        except:
            errors['client_id'] = ['Client does not exist.']

        try:
            user = User.objects.get(user_id=client.user.user_id)
        except:
            errors['user_id'] = ['User does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        user.delete()


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def unarchive_client(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        client_id = request.data.get('client_id', "")

        if not client_id:
            errors['client_id'] = ['Client ID is required.']

        try:
            client = Client.objects.get(client_id=client_id)
        except:
            errors['client_id'] = ['Client does not exist.']

        try:
            user = User.objects.get(user_id=client.user.user_id)
        except:
            errors['user_id'] = ['User does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        user.is_archived = False
        user.save()

        new_activity = AllActivity.objects.create(
            user=user,
            subject="Account UnArchived",
            body=user.email + " account archived."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

#caiesdzxsarbcray
@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def get_all_archived_clients_view2222(request):
    payload = {}
    data = {}
    errors = {}

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    all_clients = Client.objects.all().filter(user__is_archived=True)

    all_clients_serializer = AllClientsSerializer(all_clients, many=True)
    if all_clients_serializer:
        _all_clients = all_clients_serializer.data

    payload['message'] = "Successful"
    payload['data'] = _all_clients


    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([CustomJWTAuthentication, ])
def get_all_archived_clients_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    all_clients = Client.objects.all().filter(user__is_archived=True)


    if search_query:
        all_clients = all_clients.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__department__icontains=search_query) |
            Q(user__gender__icontains=search_query) |
            Q(user__dob__icontains=search_query) |
            Q(user__marital_status__icontains=search_query) |
            Q(user__phone__icontains=search_query) |
            Q(user__country__icontains=search_query) |
            Q(user__language__icontains=search_query) |
            Q(user__location_name__icontains=search_query)
        )


    paginator = Paginator(all_clients, page_size)

    try:
        paginated_clients = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_clients = paginator.page(1)
    except EmptyPage:
        paginated_clients = paginator.page(paginator.num_pages)

    all_clients_serializer = AllClientsSerializer(paginated_clients, many=True)


    data['clients'] = all_clients_serializer.data
    data['pagination'] = {
        'page_number': paginated_clients.number,
        'total_pages': paginator.num_pages,
        'next': paginated_clients.next_page_number() if paginated_clients.has_next() else None,
        'previous': paginated_clients.previous_page_number() if paginated_clients.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)






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

