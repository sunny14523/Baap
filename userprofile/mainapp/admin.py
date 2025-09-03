from django.contrib import admin
from mainapp.models import Customer,Product,Category,Cart,Order

# Register your models here.
admin_username_ans_passw_is = 'sunny and 1234'
admin.site.register(Customer)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(Order)

admin.site.register(Product)