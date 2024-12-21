from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.http import HttpResponse
from accounts.models import Profile
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
# Create your views here.
def logout_view(request):
    logout(request)  # This logs out the user
    
    return redirect('/')

@login_required(login_url='/')
def home_view(request,uuid):
    
    user_profile = get_object_or_404(Profile, email_token=uuid)
    print(user_profile.user.username)
    context={
        'user':user_profile,
        

    }
    
    print(uuid)
    print(context)
    print(user_profile)
    print(user_profile.profile_image)
    if user_profile.profile_image:  
        print("yes")
        return render(request, 'home/index.html',context)
    print("NO")
    return render(request, 'home/index.html',)


