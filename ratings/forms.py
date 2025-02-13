from django import forms
from .models import ServiceReview

class ServiceReviewForm(forms.ModelForm):
    class Meta:
        model = ServiceReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Share your experience with this service...'
            })
        }
        labels = {
            'rating': 'Rating (1-5 stars)',
            'comment': 'Your Review'
        }
