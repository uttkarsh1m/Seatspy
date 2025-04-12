from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, CustomAuthenticationForm
from .models import Profile

def home_page_view(request):
    return render(request, 'home.html')

@csrf_protect
@never_cache
@sensitive_post_parameters('password')
def custom_login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if hasattr(user, 'profile'):
                if user.profile.user_type == 'broadcaster':
                    return redirect('broadcaster_dashboard')
                else:
                    return redirect('viewer_dashboard')
            return redirect('home')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def sign_up_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            storage = messages.get_messages(request)
            for _ in storage:
                pass
            user = form.save(commit=False)
            user.save()
            user_type = form.cleaned_data.get('user_type', 'viewer')
            user.profile.user_type = user_type
            if user_type == 'broadcaster':
                user.profile.authorization_id = form.cleaned_data.get('authorization_id')
            user.profile.save()
            messages.success(request, "Signup successful! Please log in.")
            return redirect('login')
        else:
            messages.error(request, "There was an error with your signup. Please check the details and try again.")
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

def custom_logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def viewer_dashboard_view(request):
    return render(request, 'viewer/dashboard.html')

@login_required
def broadcaster_dashboard_view(request):
    return render(request, 'broadcaster/dashboard.html')

def viewer_room_view(request, roomId):
    return render(request, 'viewer/view.html', {'roomId': roomId})

def broadcaster_room_view(request, roomId):
    return render(request, 'broadcaster/broadcast.html', {'roomId': roomId})
