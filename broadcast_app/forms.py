
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re
from django.contrib.auth.forms import AuthenticationForm
from django import forms

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Email', 'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'placeholder': 'Password', 'class': 'form-control'})

class SignUpForm(UserCreationForm):
    user_type = forms.ChoiceField(choices=[('viewer', 'Viewer'),('broadcaster', 'Broadcaster')], required=True)
    authorization_id = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'user_type', 'authorization_id')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Allowed patterns and whitelist domains
        allowed_patterns = [
            r'\.ac\.in$',    # Indian academic institutions
            r'\.edu\.in$',   
            r'\.edu$',       
            r'\.iitd\.ac\.in$', r'\.iiitp\.ac\.in$', r'\.iiitl\.ac\.in$'
        ]
        whitelisted_domains = [
            'cumail.in', 'bennett.edu.in', 'ashoka.edu.in', 'vitstudent.ac.in', 
            'snu.edu.in', 'lpu.in', 'pes.edu', 'amity.edu', 'iiitd.ac.in', 
            'iiitp.ac.in', 'srmap.edu.in', 'chitkara.edu.in'
        ]
        blocked_domains = [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'rediffmail.com'
        ]

        if '@' not in email:
            raise forms.ValidationError("Invalid email format.")

        domain = email.split('@')[1]

        valid = any(re.search(pattern, email) for pattern in allowed_patterns)
        if not valid and domain not in whitelisted_domains:
            raise forms.ValidationError("Only valid college emails are allowed!")
        if domain in blocked_domains:
            raise forms.ValidationError("Only valid college emails are allowed!")
        return email

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        authorization_id = cleaned_data.get('authorization_id')

        if user_type == 'broadcaster' and not authorization_id:
            self.add_error('authorization_id', "Broadcasters must upload their authorization ID.")
        return cleaned_data
