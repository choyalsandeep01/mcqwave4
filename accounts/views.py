from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate , login , logout
from .models import Profile
from django.urls import reverse
import re
from base.email import send_account_activation_email
def sign_up(request):
    if request.user.is_authenticated:
        user_uuid = request.user.profile.email_token
        return redirect(reverse('go_to_home', kwargs={'uuid': user_uuid})) 
        
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        conf_password = request.POST.get('confirm_password')
        
        # Check if any field is empty
        if not all([first_name, last_name, username, email, password]):
            messages.warning(request, 'Please enter all the details.')
            return HttpResponseRedirect(request.path_info)
        
        # Username validation: only lowercase letters and numbers allowed
        if not re.match(r'^[a-z0-9]+$', username):
            messages.warning(request, 'Username can only contain lowercase letters and numbers, without spaces or special characters.')
            return HttpResponseRedirect(request.path_info)
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.warning(request, 'Username is already taken.')
            return HttpResponseRedirect(request.path_info)
        if User.objects.filter(email=email).exists():
            messages.warning(request, 'Email is already taken.')
            return HttpResponseRedirect(request.path_info)
        if password != conf_password:
            messages.warning(request, 'Passwords do not match.')
            return HttpResponseRedirect(request.path_info)
        # Create user if all validations pass
        user_obj = User.objects.create(first_name=first_name, last_name=last_name, email=email, username=username)
        user_obj.set_password(password)
        user_obj.save()
        
        messages.success(request, 'An email has been sent to your email address.')
        return HttpResponseRedirect(request.path_info)
        
    return render(request, 'accounts/signup.html')


def log_in(request):
    if request.user.is_authenticated:
        user_uuid = request.user.profile.email_token
        return redirect(reverse('go_to_home', kwargs={'uuid': user_uuid})) 
    if request.method == 'POST':
        username = request.POST.get('username')
        
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = User.objects.filter(username = username)

        if not user_obj.exists():
            messages.warning(request, 'Account not found.')
            return HttpResponseRedirect(request.path_info)

        
        if not user_obj[0].profile.is_email_verified:
            messages.warning(request, 'Your account is not verified.')
            return HttpResponseRedirect(request.path_info)


        

        user_obj = authenticate(username = username , password= password)
        if user_obj:
            login(request , user_obj)
            print(user_obj)
            user_uuid = user_obj.profile.email_token
            print(user_uuid)
            return redirect(reverse('go_to_home', kwargs={'uuid': user_uuid}))
            
            
            
        

        messages.warning(request, 'Invalid credentials')
        return HttpResponseRedirect(request.path_info)
    return render(request, 'accounts/login.html')


def activate_email(request , email_token):
    try:
        user = Profile.objects.get(email_token= email_token)
        user.is_email_verified = True
        user.save()
        messages.warning(request, 'Your account is verified.')

        return redirect('login')
    except Exception as e:
        return HttpResponse('Invalid Email token')


import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            # Generate a unique token
            token = str(uuid.uuid4())
            profile = user.profile
            profile.reset_token = token
            profile.save()
            usernme= user.username
            # Send reset email
            reset_link = request.build_absolute_uri(reverse('password_reset_confirm', args=[token]))
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link} for username: {usernme}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'A password reset link has been sent to your email.')
            return redirect('login')
        else:
            messages.error(request, 'No account found with that email.')

    return render(request, 'accounts/password_reset_request.html')

def password_reset_confirm(request, token):
    profile = Profile.objects.filter(reset_token=token).first()

    if not profile:
        messages.error(request, 'Invalid or expired reset token.')
        return redirect('password_reset_request')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            user = profile.user
            user.set_password(new_password)
            user.save()
            profile.reset_token = None  # Invalidate the token
            profile.save()
            messages.success(request, 'Password reset successfully. You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'accounts/password_reset_confirm.html', {'token': token})

from django.shortcuts import redirect, render
from django.contrib import messages
from .models import Profile
from django.core.exceptions import ObjectDoesNotExist
import uuid

def resend_email(request):
    if request.method == "POST":
        email = request.POST.get('email')
        
        try:
            # Check if the email exists
            user = User.objects.get(email=email)
            profile = user.profile
            
            # Check if the email is already verified
            if profile.is_email_verified:
                messages.error(request, "This email is already verified. You can log in.")
                return redirect('resend_email')

            # Generate a new token
            new_token = str(uuid.uuid4())
            profile.email_token = new_token
            profile.save()

            # Resend the activation email
            send_account_activation_email(email, new_token)
            
            messages.success(request, "A new verification email has been sent.")
            return redirect('resend_email')
        except ObjectDoesNotExist:
            messages.error(request, "No account found with this email address.")
            return redirect('resend_email')

    return render(request, 'accounts/resend_email.html')

def landing(request):
        if request.user.is_authenticated:
            user_uuid = request.user.profile.email_token
            return redirect(reverse('go_to_home', kwargs={'uuid': user_uuid})) 
        return render(request, 'home/landing.html')
