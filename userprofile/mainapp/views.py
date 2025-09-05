from calendar import error

from django.shortcuts import render,redirect,get_object_or_404

import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt



from django.shortcuts import render,redirect
from django.template.defaulttags import csrf_token
from unicodedata import category
from urllib.parse import urlencode

from .models import Customer, Cart, Product, Order , Category
from django.contrib import messages

import random
from django.core.mail import send_mail

# Create your views here.
import re
from django.core.mail import send_mail
from .models import Customer, EmailOTP  # Assuming you have this OTP model



def signup(request):
    errors = {}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        c_password = request.POST.get('c_password', '')

        # Validate name
        if not name:
            errors['name'] = 'Name is required.'
        elif not re.match(r'^[A-Za-z ]+$', name):
            errors['name'] = 'Name can only contain letters and spaces.'
        elif len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters long.'

        # Validate email
        if not email:
            errors['email'] = 'Email is required.'
        elif Customer.objects.filter(email=email).exists():
            errors['email'] = 'User already exists with this email.'

        # Validate phone
        if not phone:
            errors['phone'] = 'Phone number is required.'
        elif len(phone) != 10 or not phone.isdigit():
            errors['phone'] = 'Phone number must be 10 digits.'

        # Validate password
        if not password or not c_password:
            errors['password'] = 'Both password fields are required.'
        elif password != c_password:
            errors['password'] = 'Passwords do not match.'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters.'

        if not errors:
            # Everything is valid → send OTP
            otp = generate_otp()
            EmailOTP.objects.create(email=email, otp=otp)

            send_mail(
                'Verify your email',
                f'Your OTP code is {otp}',
                'no-reply@yourdomain.com',
                [email],
                fail_silently=False,
            )

            # Save form data in session
            request.session['signup_data'] = {
                'name': name,
                'email': email,
                'phone': phone,
                'password': password,  # optionally hash later
            }

            return redirect('verify_email_otp')  # This view should handle OTP verification and account creation

    return render(request, 'signup.html', {'errors': errors})


def login(request):
    error=''
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if Customer.objects.filter(email=email).exists() :
            customer = Customer.objects.get(email=email)
            if password == customer.password :
                print('login successful')
                request.session['user']=customer.id
                return redirect('dashboard')

            else:
                print('wrong password')
                error='Wrong Password'
        else:
            print('user does not exist')
            error= 'Invalid Email'

    return render(request,'login.html',{'error':error})



def dashboard(request):
    user_id = request.session.get('user')
    customer = Customer.objects.filter(id=user_id).first()
    category = Category.objects.all()
    selected_category = request.GET.get('category')

    if selected_category:
        product = Product.objects.filter(category__id=selected_category)
    else:
        product = Product.objects.all()

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        category_id = request.POST.get('category')  # Get category from POST

        if customer:
            cart, _ = Cart.objects.get_or_create(customer=customer)
            product_dict = cart.product_dict or {}
            product_dict[product_id] = product_dict.get(product_id, 0) + 1
            cart.product_dict = product_dict
            cart.save()

        # 🔁 Redirect to GET with category preserved
        if category_id:
            query_string = urlencode({'category': category_id})
            return redirect(f'{request.path}?{query_string}')
        else:
            return redirect(request.path)

    # Handle cart value
    cart_value = 0
    if customer and Cart.objects.filter(customer=customer).exists():
        cart = Cart.objects.get(customer=customer)
        cart_value = len(cart.product_dict)

    return render(request, 'dashboard.html', {
        'cart_value': cart_value,
        'category': category,
        'product': product
    })




def cart_view(request):
    customer = request.session.get('user')
    if not customer:
        return redirect('login')  # or wherever your login page is

    try:
        cart = Cart.objects.get(customer=customer)
    except Cart.DoesNotExist:
        cart = None

    cart_items = []
    total_price = 0

    if cart and cart.product_dict:
        for prod_id, quantity in cart.product_dict.items():
            try:
                product = Product.objects.get(id=int(prod_id))
                item_total = product.product_price * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total': item_total
                })
                total_price += item_total
            except Product.DoesNotExist:
                continue

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


@csrf_exempt

def update_cart_quantity(request):
    if request.method == 'POST':
        customer_id = request.session.get('user')
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')

        cart = Cart.objects.get(customer =customer_id)

        if product_id in cart.product_dict:
            if action == 'increase':
                cart.product_dict[product_id] += 1
            elif action == 'decrease':
                if cart.product_dict[product_id] > 1:
                    cart.product_dict[product_id] -= 1
                else:
                    del cart.product_dict[product_id]  # Remove if quantity hits 0
            cart.save()
    return redirect('cart')



@csrf_exempt
def remove_from_cart(request):
    if request.method == 'POST':
        customer_id = request.session.get('user')
        product_id = request.POST.get('product_id')

        cart = Cart.objects.get(customer_id=customer_id)
        if product_id in cart.product_dict:
            del cart.product_dict[product_id]
            cart.save()
    return redirect('cart')




def checkout_view(request):
    # Check if user is logged in
    if "user" not in request.session:
        messages.error(request, "You must be logged in to checkout.")
        return redirect('login')  # or wherever your login page is

    customer_id = request.session["user"]
    customer = Customer.objects.get(id=customer_id)
    cart = Cart.objects.filter(customer=customer).first()

    if not cart or not cart.product_dict:
        messages.error(request, "Cart is empty.")
        return redirect('dashboard')

    # Calculate total
    total = 0
    products_info = []
    for pid, qty in cart.product_dict.items():
        product = Product.objects.get(id=int(pid))
        total += product.product_price * qty
        products_info.append({'product': product, 'quantity': qty})

    total += 40  # Add shipping charge

    # Create Razorpay order
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create(dict(
        amount=int(total * 100),  # Convert to paise
        currency='INR',
        payment_capture='1'
    ))

    # Save Order in DB (initially unpaid)
    order = Order.objects.create(
        customer=customer,
        order_items=cart.product_dict,
        total_amount=total,
        phone=customer.phone,
        payment_status='Pending',
        razorpay_order_id=razorpay_order['id']
    )

    context = {
        'order': order,
        'products': products_info,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': razorpay_order['id'],
        'amount': total,
        'customer': customer,
    }

    return render(request, 'checkout.html', context)

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        order = Order.objects.get(id=order_id)
        order.payment_status = "Paid"
        order.save()

        # Clear cart
        cart = Cart.objects.filter(customer=order.customer).first()
        cart.product_dict = {}
        cart.save()

        messages.success(request, "Payment successful and order placed.")
    return redirect('dashboard')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def profile_view(request):
    customer_id = request.session.get('user')
    if not customer_id:
        return redirect('login')  # or your auth flow
    customer = Customer.objects.get(id=customer_id)
    return render(request, 'profile.html',{'customer': customer})



def personal_info(request):
    customer_id = request.session.get('user')
    if not customer_id:
        return redirect('login')  # or your auth flow
    customer = Customer.objects.get(id=customer_id)
    return render(request, 'personal_info.html', {'customer': customer})


import re  # Regular expressions


from .models import Customer, EmailOTP

import re
import random


def generate_otp():
    return str(random.randint(100000, 999999))

def edit_info(request):
    customer_id = request.session.get('user')
    if not customer_id:
        return redirect('login')

    customer = get_object_or_404(Customer, id=customer_id)
    errors = {}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        # Validate name
        if not name:
            errors['name'] = 'Name is required.'
        elif not re.match(r'^[A-Za-z ]+$', name):
            errors['name'] = 'Name can only contain letters and spaces.'
        elif len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters long.'

        # Validate email
        if not email:
            errors['email'] = 'Email is required.'

        # Validate phone
        if not phone:
            errors['phone'] = 'Phone number is required.'
        elif len(phone) != 10 or not phone.isdigit():
            errors['phone'] = 'Phone number must be 10 digits.'

        if not errors:
            if email != customer.email:
                # Check if the email already exists for another user
                if Customer.objects.filter(email=email).exclude(id=customer.id).exists():
                    errors['email'] = 'User already exists with this email.'
                else:
                    # Email changed and is unique: generate OTP and send
                    otp = generate_otp()
                    EmailOTP.objects.create(customer=customer, email=email, otp=otp)
                    send_mail(
                        'Verify your new email',
                        f'Your OTP code is {otp}',
                        'no-reply@yourdomain.com',
                        [email],
                        fail_silently=False,
                    )
                    # Save updated info in session until OTP verified
                    request.session['email_update'] = {
                        'name': name,
                        'email': email,
                        'phone': phone,
                    }
                    return redirect('verify_email_otp')
            else:
                # Email unchanged, update immediately
                customer.name = name
                customer.phone = phone
                customer.save()
                return redirect('personal_info')

    else:
        # GET request - prefill form
        name = customer.name
        email = customer.email
        phone = customer.phone

    return render(request, 'edit_info.html', {
        'name': name,
        'email': email,
        'phone': phone,
        'errors': errors,
    })


def verify_email_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        # Determine if this is signup or edit_info based on session data
        signup_data = request.session.get('signup_data')
        email_update = request.session.get('email_update')

        if signup_data:
            email = signup_data['email']
        elif email_update:
            email = email_update['email']
        else:
            return redirect('signup')  # Or redirect to appropriate page

        # Validate OTP exists for this email and matches
        try:
            otp_entry = EmailOTP.objects.get(email=email, otp=entered_otp)
        except EmailOTP.DoesNotExist:
            return render(request, 'verify_email_otp.html', {'error': 'Invalid OTP'})

        if signup_data:
            # Create new customer
            customer = Customer(
                name=signup_data['name'],
                email=signup_data['email'],
                phone=signup_data['phone'],
                password=signup_data['password'],  # Ideally hashed!
            )
            customer.save()
            del request.session['signup_data']

        elif email_update:
            # Update existing customer
            customer = Customer.objects.get(id=request.session.get('user'))
            customer.name = email_update['name']
            customer.email = email_update['email']
            customer.phone = email_update['phone']
            customer.save()
            del request.session['email_update']

        otp_entry.delete()

        return redirect('personal_info')  # or login after signup

    return render(request, 'verify_email_otp.html')





def my_orders(request):
    customer_id = request.session.get('user')
    if not customer_id:
        return redirect('login')

    orders = Order.objects.filter(customer_id=customer_id,payment_status__iexact='Paid').order_by('-created_at')

    return render(request, 'my_orders.html', {'orders': orders})


def security(request):
    return render(request, '')


def logout(request):
    request.session.flush()


    return redirect('login')


