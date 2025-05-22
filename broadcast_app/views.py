from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from .forms import SignUpForm, CustomAuthenticationForm
from .models import Profile, Broadcast
from .decorators import role_required

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

@role_required('viewer')
def viewer_dashboard_view(request):
    live_broadcasts = Broadcast.objects.filter(is_live=True).select_related('broadcaster__profile')
    return render(request, 'viewer/dashboard.html', {
        'live_broadcasts': live_broadcasts
    })
    
@role_required('broadcaster')
def broadcaster_dashboard_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            broadcast = Broadcast.objects.create(
                broadcaster=request.user,
                title=title,
            )
            broadcast.full_clean()  
            broadcast.save()
            
            return redirect('broadcaster_room', roomId=broadcast.id)

    # GET request: show existing broadcasts
    broadcasts = Broadcast.objects.filter(broadcaster=request.user).order_by('-created_at')
    return render(request, 'broadcaster/dashboard.html', {
        'broadcasts': broadcasts
    })
    
@role_required('viewer')
def viewer_room_view(request, roomId):
    broadcast = get_object_or_404(Broadcast, id=roomId)
    return render(request, 'viewer/view.html', {
        'roomId': broadcast.id,
        'title': broadcast.title,
        'broadcaster': broadcast.broadcaster.username
    })

@csrf_protect
@role_required('broadcaster')
def broadcaster_room_view(request, roomId):
    broadcast = get_object_or_404(Broadcast, id=roomId, broadcaster=request.user)
    if not broadcast.is_live:
        broadcast.is_live = True
        broadcast.save(update_fields=['is_live'])
    return render(request, 'broadcaster/broadcast.html', {
        'roomId': broadcast.id,
        'title': broadcast.title,
    })