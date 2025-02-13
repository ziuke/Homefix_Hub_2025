from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from .models import CustomUser, TenantProfile, ServiceProviderProfile
from services.models import ServiceCategory

class TenantRegistrationForm(UserCreationForm):
    location = forms.CharField(max_length=255)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'password1', 'password2', 'location')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'tenant'
        if commit:
            user.save()
            TenantProfile.objects.create(
                user=user,
                location=self.cleaned_data.get('location')
            )
        return user

class ServiceProviderRegistrationForm(UserCreationForm):
    service_location = forms.CharField(max_length=255)
    categories = forms.ModelMultipleChoiceField(
        queryset=ServiceCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select the service categories you provide"
    )
    certifications = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'password1', 'password2',
                 'service_location', 'categories', 'certifications')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'serviceprovider'
        if commit:
            user.save()
            ServiceProviderProfile.objects.create(
                user=user,
                service_location=self.cleaned_data.get('service_location'),
                certifications=self.cleaned_data.get('certifications')
            )
        return user

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if not CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("There is no user registered with this email address.")
        return email
