from django import forms
from .models import ServiceReview, DirectServiceRequestReview

class ServiceReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
    choices=[(i, str(i)) for i in range(1, 6)],
    widget=forms.RadioSelect,
    label='Rating (1-5 stars)'
    )
    class Meta:
        model = ServiceReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Share your experience with this service...'
            })
        }
        labels = {
            'comment': 'Your Review'
        }
class DirectServiceRequestReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
    choices=[(i, str(i)) for i in range(1, 6)],
    widget=forms.RadioSelect,
    label='Rating (1-5 stars)'
    )
    class Meta:
        model = DirectServiceRequestReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Share your experience with this service...'
            })
        }
        labels = {
            'comment': 'Your Review'
        }
