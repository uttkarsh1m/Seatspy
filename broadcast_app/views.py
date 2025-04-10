from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignUpForm, CustomAuthenticationForm
from .models import Profile

# ✅ Home Page View
class HomePageView(TemplateView):
    template_name = 'home.html'

# ✅ Custom LoginView
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = CustomAuthenticationForm

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        request.session.set_test_cookie()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
        login(self.request, form.get_user())

        return super().form_valid(form)  # ✅ Use `super().form_valid(form)`

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'profile'):
            if user.profile.user_type == 'broadcaster':
                return reverse_lazy('broadcaster_dashboard')  # ✅ Return URL string
            else:
                return reverse_lazy('viewer_home')  # ✅ Return URL string
        return reverse_lazy('login')  # ✅ Redirect to login if profile is missing


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('login')

def form_valid(self, form):
    # ✅ Clear existing messages (important to avoid error carryover)
    storage = messages.get_messages(self.request)
    for _ in storage:
        pass  # This clears out any previous messages

    # ✅ Save user without committing immediately to allow file processing
    user = form.save(commit=False)
    user.save()
    user_type = form.cleaned_data.get('user_type', 'viewer')

    # ✅ Update profile with user_type and authorization_id if provided
    user.profile.user_type = user_type
    if user_type == 'broadcaster':
        user.profile.authorization_id = form.cleaned_data.get('authorization_id')
    user.profile.save()

    # ✅ Success message
    messages.success(self.request, "Signup successful! Please log in.")
    return redirect(self.success_url)


    def form_invalid(self, form):
        messages.error(self.request, "There was an error with your signup. Please check the details and try again.")
        return super().form_invalid(form)


# ✅ Logout View
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

# ✅ Broadcaster Dashboard View
class BroadcasterDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'broadcaster/dashboard.html'

# ✅ Viewer Home View
class ViewerHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'viewer/viewer_home.html'
