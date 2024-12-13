from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.contrib.auth import get_user_model
User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token['user_id']
        return User.objects.get(user_id=user_id)


###############################################################################

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView, TokenVerifyView as BaseTokenVerifyView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = RefreshToken.for_user(user)

        # Customize the access token payload
        token.payload['user_id'] = user.user_id

        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class CustomTokenRefreshView(BaseTokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            token = RefreshToken(request.data.get('refresh'))
            access_token = str(token.access_token)
            return Response({'access': access_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenVerifyView(BaseTokenVerifyView):
    def post(self, request, *args, **kwargs):
        try:
            token = request.data.get('token')
            token_obj = RefreshToken(token)
            token_obj.verify()
            return Response({'message': 'Token is valid'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
