import re
from django.core.mail import send_mail
from django.contrib.auth import get_user_model, authenticate

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.api.password_views import check_email_exist
from accounts.api.serializers import UserRegistrationSerializer
from activities.models import AllActivity
from bank_account.models import BankAccount
from clients.models import Client
from weekend_chef_project.utils import convert_phone_number, generate_email_token

User = get_user_model()


@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def register_client(request):

    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        email = request.data.get('email', "").lower()
        first_name = request.data.get('first_name', "")
        last_name = request.data.get('last_name', "")
        phone = request.data.get('phone', "")
        photo = request.data.get('photo', "")
        #photo = request.FILES.get('photo')
        country = request.data.get('country', "")
        password = request.data.get('password', "")
        password2 = request.data.get('password2', "")

        phone = convert_phone_number(phone)


        if not email:
            errors['email'] = ['User Email is required.']
        elif not is_valid_email(email):
            errors['email'] = ['Valid email required.']
        elif check_email_exist(email):
            errors['email'] = ['Email already exists in our database.']

        if not first_name:
            errors['first_name'] = ['First Name is required.']

        if not last_name:
            errors['last_name'] = ['Last Name is required.']

        if not phone:
            errors['phone'] = ['Phone number is required.']

        if not country:
            errors['country'] = ['Country is required.']


        if not password:
            errors['password'] = ['Password is required.']

        if not password2:
            errors['password2'] = ['Password2 is required.']

        if password != password2:
            errors['password'] = ['Passwords dont match.']

        if not is_valid_password(password):
            errors['password'] = ['Password must be at least 8 characters long\n- Must include at least one uppercase letter,\n- One lowercase letter, one digit,\n- And one special character']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            data["user_id"] = user.user_id
            data["email"] = user.email
            data["first_name"] = user.first_name
            data["last_name"] = user.last_name

            user.user_type = "Client"
            user.phone=phone
            if photo:
                user.photo=photo
            user.country=country
            user.save()



            client = Client.objects.create(
                user=user,
            )
            client.save()



            new_bank_account = BankAccount.objects.create(
                user=user,
                balance=10000000000

            )

            data['phone'] = user.phone
            data['country'] = user.country
            data['photo'] = user.photo.url
            data['account_id'] = new_bank_account.account_id

        token = Token.objects.get(user=user).key
        data['token'] = token

        email_token = generate_email_token()

        user = User.objects.get(email=email)
        user.email_token = email_token
        user.save()


        ##### SEND SMS

        #_msg = f'Your Weekend Chef OTP code is {email_token}'
        #url = f"https://apps.mnotify.net/smsapi"
        #api_key = settings.MNOTIFY_KEY  # Replace with your actual API key
#
        #print(api_key)
        #response = requests.post(url,
        #data={
        #    "key": api_key,
        #    "to": user.phone,
        #    "msg": _msg,
        #    "sender_id": settings.MNOTIFY_SENDER_ID,
        #    })
        #if response.status_code == 200:
        #    print('##########################')
        #    print(response.content)
        #    payload['message'] = "Successful"
        #else:
        #    errors['user_id'] = ['Failed to send SMS']
#
        #    ######################


        context = {
            'email_token': email_token,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        # ##
        txt_ = get_template("registration/emails/verify.txt").render(context)
        html_ = get_template("registration/emails/verify.html").render(context)
        # ##
        subject = 'EMAIL CONFIRMATION CODE'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]



        # # Use Celery chain to execute tasks in sequence
        # email_chain = chain(
        #     send_generic_email.si(subject, txt_, from_email, recipient_list, html_),
        # )
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





        new_activity = AllActivity.objects.create(
            user=user,
            subject="User Registration",
            body=user.email + " Just created an account."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)





class ClientLogin(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = {}
        data = {}
        errors = {}


        email = request.data.get('email', '').lower()
        password = request.data.get('password', '')
        fcm_token = request.data.get('fcm_token', '')

        if not email:
            errors['email'] = ['Email is required.']

        if not password:
            errors['password'] = ['Password is required.']

        if not fcm_token:
            errors['fcm_token'] = ['FCM device token is required.']

        try:
            qs = User.objects.filter(email=email)
        except User.DoesNotExist:
            errors['email'] = ['User does not exist.']



        if qs.exists():
            not_active = qs.filter(email_verified=False)
            if not_active:
                errors['email'] = ["Please check your email to confirm your account or resend confirmation email."]

        if not check_password(email, password):
            errors['password'] = ['Invalid Credentials']

        user = authenticate(email=email, password=password)


        if not user:
            errors['email'] = ['Invalid Credentials']



        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        try:
            token = Token.objects.get(user=user)
        except Token.DoesNotExist:
            token = Token.objects.create(user=user)

        user.fcm_token = fcm_token
        user.save()


        data["user_id"] = user.user_id
        data["email"] = user.email
        data["first_name"] = user.first_name
        data["last_name"] = user.last_name
        data["photo"] = user.photo.url
        data["country"] = user.country
        data["phone"] = user.phone
        data["token"] = token.key

        payload['message'] = "Successful"
        payload['data'] = data

        new_activity = AllActivity.objects.create(
            user=user,
            subject="Client Login",
            body=user.email + " Just logged in."
        )
        new_activity.save()

        return Response(payload, status=status.HTTP_200_OK)



@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def archive_user_view(request):

    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        user_id = request.data.get('user_id', "")


        if not user_id:
            errors['user_id'] = ['User ID is required.']

        try:
            user = User.objects.get(user_id=user_id)
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
            subject="User Archived",
            body=user.email + " account is archived."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def remove_user_view(request):

    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        user_id = request.data.get('user_id', "")


        if not user_id:
            errors['user_id'] = ['User ID is required.']

        try:
            user = User.objects.get(user_id=user_id)
        except:
            errors['user_id'] = ['User does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        user.is_deleted = True
        user.save()

        new_activity = AllActivity.objects.create(
            user=user,
            subject="User Removed",
            body=user.email + " Just deleted their account."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def verify_client_email(request):
    payload = {}
    data = {}
    errors = {}

    email_errors = []
    token_errors = []

    email = request.data.get('email', '').lower()
    email_token = request.data.get('email_token', '')

    if not email:
        email_errors.append('Email is required.')

    qs = User.objects.filter(email=email)
    if not qs.exists():
        email_errors.append('Email does not exist.')

    if email_errors:
        errors['email'] = email_errors

    if not email_token:
        token_errors.append('Token is required.')

    user = None
    if qs.exists():
        user = qs.first()
        if email_token != user.email_token:
            token_errors.append('Invalid Token.')

    if token_errors:
        errors['email_token'] = token_errors

    if email_errors or token_errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)



    try:
        token = Token.objects.get(user=user)
    except Token.DoesNotExist:
        token = Token.objects.create(user=user)

    user.is_active = True
    user.email_verified = True
    user.save()

    data["user_id"] = user.user_id
    data["email"] = user.email
    data["first_name"] = user.first_name
    data["last_name"] = user.last_name
    data["photo"] = user.photo.url
    data["token"] = token.key

    payload['message'] = "Successful"
    payload['data'] = data

    new_activity = AllActivity.objects.create(
        user=user,
        subject="Verify Email",
        body=user.email + " just verified their email",
    )
    new_activity.save()

    return Response(payload, status=status.HTTP_200_OK)




@api_view(['POST', ])
@permission_classes([AllowAny])
@authentication_classes([])
def resend_client_email_verification(request):
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
    otp_code = generate_email_token()
    user.email_token = otp_code
    user.save()



     ##### SEND SMS

    # _msg = f'Your Weekend Chef OTP code is {otp_code}'
    # url = f"https://apps.mnotify.net/smsapi"
    # api_key = settings.MNOTIFY_KEY  # Replace with your actual API key
    # print(api_key)
    # response = requests.post(url,
    # data={
    #     "key": api_key,
    #     "to": user.phone,
    #     "msg": _msg,
    #     "sender_id": settings.MNOTIFY_SENDER_ID,
    #     })
    # if response.status_code == 200:
    #     print('##########################')
    #     print(response.content)
    #     payload['message'] = "Successful"
    # else:
    #     errors['user_id'] = ['Failed to send SMS']
    #     ######################


    context = {
        'email_token': otp_code,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name
    }
#
    txt_ = get_template("registration/emails/verify.txt").render(context)
    html_ = get_template("registration/emails/verify.html").render(context)
#
    subject = 'OTP CODE'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

     # Use Celery chain to execute tasks in sequence
    # email_chain = chain(
    #      send_generic_email.si(subject, txt_, from_email, recipient_list, html_),
    #   )
    #  # Execute the Celery chain asynchronously
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
        subject="Email verification sent",
        body="Email verification sent to " + user.email,
    )
    new_activity.save()

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


def check_password(email, password):

    try:
        user = User.objects.get(email=email)
        return user.check_password(password)
    except User.DoesNotExist:
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



