from django.db import models

from shop.models import Shop


# Create your models here.

class PaymentSetup(models.Model):
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='shop_payment_setup')
    platform = models.CharField(max_length=200,  null=True, blank=True)
    private_api_key = models.CharField(max_length=1000, null=True, blank=True)
    public_api_key = models.CharField(max_length=1000, null=True, blank=True)
    
    reservation_policy_value = models.IntegerField(default=0)
    reservation_policy_description = models.TextField(null=True, blank=True)
    
    cancellation_policy_value = models.IntegerField(default=0)
    cancellation_policy_description = models.TextField(null=True, blank=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)