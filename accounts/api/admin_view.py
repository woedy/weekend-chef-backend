from django.core.mail import send_mail

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

from accounts.api.client_views import check_password, is_valid_email, is_valid_password
from accounts.api.password_views import check_email_exist
from accounts.api.serializers import UserRegistrationSerializer
from activities.models import AllActivity
from bank_account.models import BankAccount
from week_admin.models import WeekendChefAdmin
from weekend_chef_project.utils import generate_email_token
from django.core.mail import send_mail
from django.contrib.auth import get_user_model, authenticate


from rest_framework.views import APIView

from accounts.api.serializers import UserRegistrationSerializer
from activities.models import AllActivity
from bank_account.models import BankAccount
from weekend_chef_project.utils import generate_email_token


User = get_user_model()



@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def register_weekend_chef_admin(request):

    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        email = request.data.get('email', "").lower()
        first_name = request.data.get('first_name', "")
        last_name = request.data.get('last_name', "")
        phone = request.data.get('phone', "")
        photo = request.FILES.get('photo')
        country = request.data.get('country', "")
        password = request.data.get('password', "")
        password2 = request.data.get('password2', "")


        if not email:
            errors['email'] = ['User Email is required.']
        elif not is_valid_email(email):
            errors['email'] = ['Valid email required.']
        elif check_email_exist(email):
            errors['email'] = ['Email already exists in our database.']

        if not first_name:
            errors['first_name'] = ['First Name is required.']

        if not last_name:
            errors['last_name'] = ['last Name is required.']

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
            data["country"] = user.country
            data["photo"] = user.photo

            user.user_type = "Admin"
            user.save()

            admin_profile = WeekendChefAdmin.objects.create(
                user=user

            )
            admin_profile.save()

            new_bank_account = BankAccount.objects.create(
                user=user,

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

        context = {
            'email_token': email_token,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
#
        txt_ = get_template("registration/emails/verify.txt").render(context)
        html_ = get_template("registration/emails/verify.html").render(context)
#
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



#
        new_activity = AllActivity.objects.create(
            user=user,
            subject="User Registration",
            body=user.email + " Just created an account."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


class AdminLogin(APIView):
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
            subject="Admin Login",
            body=user.email + " Just logged in."
        )
        new_activity.save()

        return Response(payload, status=status.HTTP_200_OK)

