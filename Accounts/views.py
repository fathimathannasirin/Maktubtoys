from django.shortcuts import render,redirect,get_object_or_404
from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account, UserProfile, ContactMessage
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from carts.models import Cart,CartItem

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.http import HttpResponse

from carts.views import _cart_id
import requests
from orders.models import Order,OrderProduct

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name =form.cleaned_data['first_name']
            last_name =form.cleaned_data['last_name']
            phone_number =form.cleaned_data['phone_number']
            email =form.cleaned_data['email']
            password =form.cleaned_data['password']
            username = email.split("@")[0]
            user =Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.png'
            profile.save()


            current_site = get_current_site(request)
            mail_subject = 'please activate your account'
            message = render_to_string('accounts/account_verification_email.html',{
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Thankyou for registering with us. We have sent a verification email to your email address. Please verify it.')
            return redirect('/en/accounts/login/?command=verification&email=' + email)
    else:
        form = RegistrationForm()
    context={
        'form': form,
    }
    return render(request, 'accounts/register.html',context)

from django.contrib import auth

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = auth.authenticate(email=email, password=password)
        
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exits = CartItem.objects.filter( cart=cart).exists()
                if is_cart_item_exits:
                    cart_item = CartItem.objects.filter(cart=cart)

                    #getting the product variations by cart id
                    product_variation =[]
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                        # ge the cart items from the user to access his product variatons
                        cart_item = CartItem.objects.filter( user=user)
                        ex_var_list =[]
                        id =[]
                        for item in cart_item:
                            existing_variation = item.variations.all()
                            ex_var_list.append (list(existing_variation))
                            id.append(item.id)

                        for pr in product_variation:
                            if pr in ex_var_list:
                                index=ex_var_list.index(pr)
                                item_id = id[index]
                                item= CartItem.objects.get(id=item_id)
                                item.quantity += 1
                                item.user = user
                                item.save()
                            else:
                                cart_item = CartItem.objects.filter(cart=cart)
                                for item in cart_item:
                                    item.user=user
                                    item.save()
            except:
                pass
            if user is not None:
                auth.login(request, user)
                messages.success(request, 'You are now logged in.')
                
                # Check if 'next' is in the URL parameters (e.g., /login/?next=/cart/checkout/)
                next_page = request.GET.get('next')
                
                if next_page:
                    return redirect(next_page)
                else:
                    return redirect('home') # Fallback if no 'next' parameter exists
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')           
    return render(request, 'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request,'you are logged out.')
    return redirect('login') 

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')
    
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    userprofile = UserProfile.objects.get(user_id=request.user.id)
    context ={
        'orders_count' : orders_count,
        'userprofile' : userprofile,
    }
    return render(request, 'accounts/dashboard.html', context)

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            
            # reset password
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html',{
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request,'Account does not exist!')
            return redirect('forgotPassword')
    return render(request,'accounts/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid']=uid
        messages.success(request, 'please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'this link has been expired!')
        return redirect('login')
    
def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset seccessful')
            return redirect('login')
        else:
            messages.error(request, 'password do not match!')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context ={
        'orders' : orders,
    }
    return render(request, 'accounts/my_orders.html', context)

@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context ={
        'user_form' : user_form,
        'profile_form' : profile_form,
        'userprofile' : userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def Change_Password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        # 1. Check if New Password and Confirm Password match
        if new_password == confirm_password:
            user = Account.objects.get(username__exact=request.user.username)
            
            # 2. Check if the "Current Password" provided is actually correct
            if user.check_password(current_password):
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully.')
                return redirect('Change_Password')
            else:
                # This triggers if "Current Password" is wrong
                messages.error(request, 'The current password you entered is incorrect.')
                return redirect('Change_Password')
        else:
            # This triggers if New and Confirm passwords don't match
            messages.error(request, 'New password and confirmation do not match!')
            return redirect('Change_Password')
            
    return render(request, 'accounts/Change_Password.html')

@login_required(login_url='login')
def order_detail(request, order_id):
    try:
        # Allows Admin to see any order; customers can only see their own
        if request.user.is_staff:
            order = Order.objects.get(order_number=order_id)
        else:
            order = Order.objects.get(order_number=order_id, user=request.user)
            
        order_detail = OrderProduct.objects.filter(order=order)
        
        # Detects if the 'VIEW INVOICE' button was clicked in the Admin
        is_admin_view = request.GET.get('mode') == 'admin'

        context = {
            'order_detail': order_detail,
            'order': order,
            'is_admin_view': is_admin_view,
        }
        if is_admin_view:
            return render(request, 'orders/admin_invoice_pdf.html', context)
        return render(request, 'accounts/order_detail.html', context)
    except Order.DoesNotExist:
        return redirect('my_orders')
    
def contact_us(request):
    if request.method == 'POST':
        # 1. Capture the data from the HTML form
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # 2. Save to the database
        contact = ContactMessage(
            name=name, 
            email=email, 
            subject=subject, 
            message=message
        )
        contact.save()

        # 3. Show success message
        messages.success(request, 'Thank you for contacting us. We will get back to you shortly.')
        return redirect('contact_us')
        
    return render(request, 'accounts/contact_us.html')