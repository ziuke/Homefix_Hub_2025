from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg
from services.models import ServiceRequest
from .models import ServiceReview
from .forms import ServiceReviewForm

# Create your views here.

@login_required
def create_review(request, service_request_id):
    service_request = get_object_or_404(
        ServiceRequest,
        id=service_request_id,
        tenant=request.user,
        status='completed'
    )
    
    if hasattr(service_request, 'review'):
        messages.error(request, 'You have already reviewed this service.')
        return redirect('services:request_detail', pk=service_request.id)
    
    if request.method == 'POST':
        form = ServiceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.service_request = service_request
            review.reviewer = request.user
            review.save()
            
            messages.success(request, 'Thank you for your review!')
            return redirect('services:request_detail', pk=service_request.id)
    else:
        form = ServiceReviewForm()
    
    return render(request, 'ratings/review_form.html', {
        'form': form,
        'service_request': service_request
    })

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(
        ServiceReview,
        id=review_id,
        reviewer=request.user
    )
    
    if request.method == 'POST':
        form = ServiceReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated.')
            return redirect('services:request_detail', pk=review.service_request.id)
    else:
        form = ServiceReviewForm(instance=review)
    
    return render(request, 'ratings/review_form.html', {
        'form': form,
        'service_request': review.service_request,
        'is_edit': True
    })

def provider_reviews(request, provider_id):
    reviews = ServiceReview.objects.filter(
        service_request__provider_id=provider_id
    ).select_related('reviewer', 'service_request', 'service_request__category')
    
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    return render(request, 'ratings/provider_reviews.html', {
        'reviews': reviews,
        'avg_rating': avg_rating
    })
