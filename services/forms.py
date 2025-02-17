from django import forms
from .models import ServiceRequest, ServiceOffer, ServiceReview, ServiceMessage, ProviderProfile, ServiceCategory
from django.utils.timezone import now
from django.core.exceptions import ValidationError

class ServiceRequestForm(forms.ModelForm):
    category = forms.ModelMultipleChoiceField(
        queryset=ServiceCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = ServiceRequest
        fields = ['category', 'title', 'description', 'location', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ServiceOfferForm(forms.ModelForm):
    proposed_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Enter the proposed cost for this service",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',  # Bootstrap styling
            'placeholder': 'Enter cost'
        })
    )
    proposed_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        help_text="Select the proposed date for the service"
    )
    proposed_time_slot = forms.CharField(
        max_length=50,
        help_text="e.g., 'Morning (9AM-12PM)', 'Afternoon (1PM-5PM)'",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter time slot'
        })
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional details (optional)'
        }),
        required=False,
        help_text="Additional details about your offer (optional)"
    )

    def clean_proposed_date(self):
        proposed_date = self.cleaned_data.get('proposed_date')
        if proposed_date and proposed_date < now().date():
            raise ValidationError("The proposed date cannot be in the past.")
        return proposed_date

    class Meta:
        model = ServiceOffer
        fields = ['proposed_cost', 'proposed_date', 'proposed_time_slot', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set dynamic min date for proposed_date field
        self.fields['proposed_date'].widget.attrs['min'] = now().date().isoformat()


class ServiceReviewForm(forms.ModelForm):
    class Meta:
        model = ServiceReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

class ServiceMessageForm(forms.ModelForm):
    class Meta:
        model = ServiceMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Type your message here...'}),
        }

class ProviderProfileForm(forms.ModelForm):
    class Meta:
        model = ProviderProfile
        fields = ['categories', 'is_available']
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categories'].help_text = "Select all service categories you can provide"

class ServiceProviderSearchForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=None,
        empty_label="All Categories",
        required=False
    )
    location = forms.CharField(required=False)
    rating = forms.ChoiceField(
        choices=[
            ('', 'Any Rating'),
            ('4', '4+ Stars'),
            ('3', '3+ Stars'),
            ('2', '2+ Stars'),
        ],
        required=False
    )
    availability = forms.BooleanField(required=False, label='Available Now')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import ServiceCategory
        self.fields['category'].queryset = ServiceCategory.objects.all()


from .models import DirectServiceRequest

class DirectServiceRequestForm(forms.ModelForm):
    class Meta:
        model = DirectServiceRequest
        fields = ['message']  # Only the message is entered by the tenant
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter any additional details (optional)...'}),
        }