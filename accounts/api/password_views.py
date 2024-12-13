import re
from django.core.mail import EmailMessage, send_mail

from celery import chain
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.template.loader import get_template
import requests
from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.api.serializers import UserRegistrationSerializer, PasswordResetSerializer
from activities.models import AllActivity
from bank_account.models import BankAccount
from clients.models import Client
from week_admin.models import WeekendChefAdmin
from weekend_chef_project.utils import convert_phone_number, generate_email_token, generate_random_otp_code

User = get_user_model()




class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer



    def post(self, request, *args, **kwargs):
        payload = {}
        data = {}
        errors = {}
        email_errors = []

        email = request.data.get('email', '').lower()

        if not email:
            email_errors.append('Email is required.')
        if email_errors:
            errors['email'] = email_errors
            payload['message'] = "Error"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_404_NOT_FOUND)

        qs = User.objects.filter(email=email)
        if not qs.exists():
            email_errors.append('Email does not exist.')
            if email_errors:
                errors['email'] = email_errors
                payload['message'] = "Error"
                payload['errors'] = errors
                return Response(payload, status=status.HTTP_404_NOT_FOUND)


        user = User.objects.filter(email=email).first()
        otp_code = generate_random_otp_code()
        user.otp_code = otp_code
        user.save()

        context = {
            'otp_code': otp_code,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }

        txt_ = get_template("registration/emails/send_otp.txt").render(context)
        html_ = get_template("registration/emails/send_otp.html").render(context)

        subject = 'OTP CODE'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        # # Use Celery chain to execute tasks in sequence
        # email_chain = chain(
        #     send_generic_email.si(subject, txt_, from_email, recipient_list, html_),
        #  )
        # # Execute the Celery chain asynchronously
        # email_chain.apply_async()

        send_mail(
            subject,
            txt_,
            from_email,
            recipient_list,
            html_message=html_,
            fail_silently=False,
        )

       # data["otp_code"] = otp_code
        data["email"] = user.email
        data["user_id"] = user.user_id

        new_activity = AllActivity.objects.create(
            user=user,
            subject="Reset Password",
            body="OTP sent to " + user.email,
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

        return Response(payload, status=status.HTTP_200_OK)



@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def confirm_otp_password_view(request):
    payload = {}
    data = {}
    errors = {}

    email_errors = []
    otp_errors = []

    email = request.data.get('email', '').lower()
    otp_code = request.data.get('otp_code', '')

    if not email:
        email_errors.append('Email is required.')

    if not otp_code:
        otp_errors.append('OTP code is required.')

    user = User.objects.filter(email=email).first()

    if user is None:
        email_errors.append('Email does not exist.')

    client_otp = user.otp_code if user else ''

    if client_otp != otp_code:
        otp_errors.append('Invalid Code.')

    if email_errors or otp_errors:
        errors['email'] = email_errors
        errors['otp_code'] = otp_errors
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    data['email'] = user.email if user else ''
    data['user_id'] = user.user_id if user else ''

    payload['message'] = "Successful"
    payload['data'] = data
    return Response(payload, status=status.HTTP_200_OK)



@api_view(['POST', ])
@permission_classes([AllowAny])
@authentication_classes([])
def resend_password_otp(request):
    payload = {}
    data = {}
    errors = {}
    email_errors = []


    email = request.data.get('email', '').lower()

    if not email:
        email_errors.append('Email is required.')
    if email_errors:
        errors['email'] = email_errors
        payload['message'] = "Error"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    qs = User.objects.filter(email=email)
    if not qs.exists():
        email_errors.append('Email does not exist.')
        if email_errors:
            errors['email'] = email_errors
            payload['message'] = "Error"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_404_NOT_FOUND)

    user = User.objects.filter(email=email).first()
    otp_code = generate_random_otp_code()
    user.otp_code = otp_code
    user.save()

    context = {
        'otp_code': otp_code,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name
    }

    txt_ = get_template("registration/emails/send_otp.txt").render(context)
    html_ = get_template("registration/emails/send_otp.html").render(context)

    subject = 'OTP CODE'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    # # Use Celery chain to execute tasks in sequence
    # email_chain = chain(
    #     send_generic_email.si(subject, txt_, from_email, recipient_list, html_),
    #  )
    # # Execute the Celery chain asynchronously
    # email_chain.apply_async()

    send_mail(
        subject,
        txt_,
        from_email,
        recipient_list,
        html_message=html_,
        fail_silently=False,
    )

    #data["otp_code"] = otp_code
    data["email"] = user.email
    data["user_id"] = user.user_id

    new_activity = AllActivity.objects.create(
        user=user,
        subject="Password OTP sent",
        body="Password OTP sent to " + user.email,
    )
    new_activity.save()

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['POST', ])
@permission_classes([AllowAny])
@authentication_classes([])
def new_password_reset_view(request):
    payload = {}
    data = {}
    errors = {}
    email_errors = []
    password_errors = []

    email = request.data.get('email', '0').lower()
    new_password = request.data.get('new_password')
    new_password2 = request.data.get('new_password2')



    if not email:
        email_errors.append('Email is required.')
        if email_errors:
            errors['email'] = email_errors
            payload['message'] = "Error"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_404_NOT_FOUND)

    qs = User.objects.filter(email=email)
    if not qs.exists():
        email_errors.append('Email does not exists.')
        if email_errors:
            errors['email'] = email_errors
            payload['message'] = "Error"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_404_NOT_FOUND)


    if not new_password:
        password_errors.append('Password required.')
        if password_errors:
            errors['password'] = password_errors
            payload['message'] = "Error"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_404_NOT_FOUND)


    if new_password != new_password2:
        password_errors.append('Password don\'t match.')
        if password_errors:
            errors['password'] = password_errors
            payload['message'] = "Error"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_404_NOT_FOUND)

    user = User.objects.filter(email=email).first()
    user.set_password(new_password)
    user.save()

    data['email'] = user.email
    data['user_id'] = user.user_id


    payload['message'] = "Successful, Password reset successfully."
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)







def check_email_exist(email):

    qs = User.objects.filter(email=email)
    if qs.exists():
        return True
    else:
        return False


def is_valid_email(email):
    # Regular expression pattern for basic email validation
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    # Using re.match to check if the email matches the pattern
    if re.match(pattern, email):
        return True
    else:
        return False


def is_valid_password(password):
    # Check for at least 8 characters
    if len(password) < 8:
        return False

    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False

    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False

    # Check for at least one digit
    if not re.search(r'[0-9]', password):
        return False

    # Check for at least one special character
    if not re.search(r'[-!@#\$%^&*_()-+=/.,<>?"~`£{}|:;]', password):
        return False

    return True




