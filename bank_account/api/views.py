# views.py

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .serializers import (
    TransactionSerializer,
    DepositSerializer,
    WithdrawSerializer,
    TransferSerializer
)
from ..models import BankAccount
from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_account_balance_view(request, account_id):
    try:
        bank_account = BankAccount.objects.get(account_id=account_id)
    except BankAccount.DoesNotExist:
        return Response({'message': 'Bank account not found'}, status=status.HTTP_404_NOT_FOUND)

    balance = bank_account.balance
    return Response({'account_id': account_id, 'balance': balance}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def list_transactions_view(request, account_id):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    try:
        bank_account = BankAccount.objects.get(account_id=account_id)
    except BankAccount.DoesNotExist:
        errors['message'] = "Bank account not found"
        return Response(errors, status=status.HTTP_404_NOT_FOUND)

    transactions = bank_account.transactions.all().order_by("-timestamp")

    if search_query:
        transactions = transactions.filter(
            description__icontains=search_query
        )

    paginator = Paginator(transactions, page_size)

    try:
        paginated_transactions = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_transactions = paginator.page(1)
    except EmptyPage:
        paginated_transactions = paginator.page(paginator.num_pages)

    transactions_serializer = TransactionSerializer(paginated_transactions, many=True)

    data['transactions'] = transactions_serializer.data
    data['pagination'] = {
        'page_number': paginated_transactions.number,
        'total_pages': paginator.num_pages,
        'next': paginated_transactions.next_page_number() if paginated_transactions.has_next() else None,
        'previous': paginated_transactions.previous_page_number() if paginated_transactions.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def client_list_transactions_view(request, user_id):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    try:
        user = User.objects.get(user_id=user_id)
    except:
        errors['user_id'] = ['User does not exist.']

    try:
        bank_account = BankAccount.objects.get(user=user)
    except BankAccount.DoesNotExist:
        errors['user_id'] = ['Bank Account does not exist.']

    transactions = bank_account.transactions.all().order_by("-timestamp")

    balance = bank_account.balance
    account_id = bank_account.account_id
    data['balance'] = balance
    data['account_id'] = account_id


    if search_query:
        transactions = transactions.filter(
            description__icontains=search_query
        )

    paginator = Paginator(transactions, page_size)

    try:
        paginated_transactions = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_transactions = paginator.page(1)
    except EmptyPage:
        paginated_transactions = paginator.page(paginator.num_pages)

    transactions_serializer = TransactionSerializer(paginated_transactions, many=True)

    data['transactions'] = transactions_serializer.data
    data['pagination'] = {
        'page_number': paginated_transactions.number,
        'total_pages': paginator.num_pages,
        'next': paginated_transactions.next_page_number() if paginated_transactions.has_next() else None,
        'previous': paginated_transactions.previous_page_number() if paginated_transactions.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def deposit_view(request, account_id):
    try:
        account = BankAccount.objects.get(account_id=account_id)
    except BankAccount.DoesNotExist:
        return Response({'message': 'Bank account not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = DepositSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        if account.deposit(amount, description):
            return Response({'message': 'Deposit successful'}, status=status.HTTP_200_OK)
        return Response({'message': 'Deposit failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def withdraw_view(request, account_id):
    try:
        account = BankAccount.objects.get(account_id=account_id)
    except BankAccount.DoesNotExist:
        return Response({'message': 'Bank account not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = WithdrawSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        if account.withdraw(amount, description):
            return Response({'message': 'Withdrawal successful'}, status=status.HTTP_200_OK)
        return Response({'message': 'Withdrawal failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def transfer_view(request, account_id):
    try:
        from_account = BankAccount.objects.get(account_id=account_id)
    except BankAccount.DoesNotExist:
        return Response({'message': 'Bank account not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = TransferSerializer(data=request.data)
    if serializer.is_valid():
        to_account_id = serializer.validated_data['to_account_id']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')

        try:
            to_account = BankAccount.objects.get(account_id=to_account_id)
        except BankAccount.DoesNotExist:
            return Response({'message': 'Destination account not found'}, status=status.HTTP_404_NOT_FOUND)

        if from_account.withdraw(amount, f'Transfer to {to_account_id}'):
            to_account.deposit(amount, f'Transfer from {account_id}')
            return Response({'message': 'Transfer successful'}, status=status.HTTP_200_OK)
        return Response({'message': 'Transfer failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def client_deposit_view(request, user_id):
    errors = {}
    payload = {}



    try:
        user = User.objects.get(user_id=user_id)
    except:
        errors['user_id'] = ['User does not exist.']





    try:
        account = BankAccount.objects.get(user=user)
    except BankAccount.DoesNotExist:
        errors['user_id'] = ['Bank Account does not exist.']


    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)


    serializer = DepositSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        if account.deposit(amount, description):
            return Response({'message': 'Deposit successful'}, status=status.HTTP_200_OK)
        return Response({'message': 'Deposit failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def client_withdraw_view(request, user_id):


    errors = {}
    payload = {}




    try:
        user = User.objects.get(user_id=user_id)
    except:
        errors['user_id'] = ['User does not exist.']





    try:
        account = BankAccount.objects.get(user=user)
    except BankAccount.DoesNotExist:
        errors['user_id'] = ['Bank Account does not exist.']


    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)


    serializer = WithdrawSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        if account.withdraw(amount, description):
            return Response({'message': 'Withdrawal successful'}, status=status.HTTP_200_OK)
        return Response({'message': 'Withdrawal failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
