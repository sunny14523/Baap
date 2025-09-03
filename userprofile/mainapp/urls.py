from django.contrib import admin
from django.urls import path
from mainapp import views

urlpatterns = [
    path('', views.login,name='login' ),
    path('signup/', views.signup, name='signup'),

    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/update/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),

    path('profile/', views.profile_view, name='profile'),
    path('personal-info/', views.personal_info, name='personal_info'),
    path('edit-info/', views.edit_info, name='edit_info'),
    path('verify-email-otp/', views.verify_email_otp, name='verify_email_otp'),

    path('my-orders/', views.my_orders, name='my_orders'),


    path('profile/my-orders/', views.my_orders, name='my_orders'),
    path('profile/security/', views.security, name='security'),

    # path('checkout/', views.checkout_view, name='checkout'),  # optional


]
