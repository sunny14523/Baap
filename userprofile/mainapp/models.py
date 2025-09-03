from django.db import models
from django.contrib.auth.hashers import make_password, check_password


# Create your models here.

class Customer(models.Model):

    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=10)
    email = models.EmailField()
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.name
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)




class Cart(models.Model):

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product_dict = models.JSONField(default=dict, null=True)

    def __str__(self):
        return self.customer.name


class Category(models.Model):
    category_name = models.CharField(max_length=100)

    def __str__(self):
        return self.category_name


class Product(models.Model):

    product_name = models.CharField(max_length=100)
    product_price = models.IntegerField(max_length=100)
    product_des = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_img = models.ImageField(upload_to='product_images/',null=True)

    def __str__(self):
        return self.product_name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order_items = models.JSONField(default=dict)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone = models.CharField(max_length=15)
    payment_status = models.CharField(max_length=20, default='Pending')  # e.g. Paid, Failed
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(max_length=100, default='order_placed')

    def __str__(self):
        return f"Order #{self.id} by {self.customer.name}"



from django.utils import timezone
from datetime import timedelta

class EmailOTP(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)  # OTP valid for 10 mins

    def __str__(self):
        return f"OTP for {self.email} ({'Verified' if self.verified else 'Not verified'})"
