from django import forms
from .models import TenantProfile, ServiceProviderProfile
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from .models import CustomUser
from services.models import ServiceCategory

class TenantRegistrationForm(UserCreationForm):
    location = forms.CharField(max_length=255)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'tenant'
        if commit:
            user.save()
            TenantProfile.objects.create(
                user=user
            )
        return user

class ServiceProviderRegistrationForm(UserCreationForm):
    service_location = forms.CharField(max_length=255)
    categories = forms.ModelMultipleChoiceField(
        queryset=ServiceCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Change to SelectMultiple if needed
        required=True,
        help_text="Select the service categories you provide"
    )
    certifications = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'serviceprovider'
        if commit:
            user.save()
            ServiceProviderProfile.objects.create(
                user=user
            )
        return user
class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if not CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("There is no user registered with this email address.")
        return email



class TenantProfileForm(forms.ModelForm):
    """Form for Tenants to update their profile."""
    
    class Meta:
        model = TenantProfile
        fields = ['location']
        widgets = {
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring focus:ring-indigo-300 focus:border-indigo-500',
                'placeholder': 'Enter your location'
            }),
        }


class ServiceProviderProfileForm(forms.ModelForm):
    """Form for Service Providers to update their profile."""
    
    service_provided = forms.ModelMultipleChoiceField(
        queryset=ServiceCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'}),
        required=False
    )

    class Meta:
        model = ServiceProviderProfile
        fields = ['service_location', 'service_provided', 'certifications']
        widgets = {
            'service_location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring focus:ring-indigo-300 focus:border-indigo-500',
                'placeholder': 'Enter your location'
            }),
            'certifications': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring focus:ring-indigo-300 focus:border-indigo-500',
                'rows': 4,
                'placeholder': 'List your certifications'
            }),
        }

    def clean_service_provided(self):
        """Ensure only IDs are stored in the database."""
        service_categories = self.cleaned_data.get('service_provided', [])
        return [category.id for category in service_categories]
