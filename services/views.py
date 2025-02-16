from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.utils import timezone
import json
from django.contrib import messages
from .models import (
    ServiceRequest, ServiceOffer, ProviderProfile, 
    ServiceCategory, ServiceMessage
)
from .forms import (
    ServiceRequestForm, ServiceOfferForm, ServiceMessageForm,
    ProviderProfileForm, ServiceProviderSearchForm
)
from ratings.forms import ServiceReviewForm
from ratings.models import ServiceReview
from chat.models import ChatRoom

@login_required
def service_request_create(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.tenant = request.user
            service_request.save()
            messages.success(request, 'Service request created successfully!')
            return redirect('services:request_detail', pk=service_request.pk)
    else:
        form = ServiceRequestForm()
    return render(request, 'services/request_form.html', {'form': form})

@login_required
def service_request_list(request):
    if request.user.user_type == 'tenant':
        requests = ServiceRequest.objects.filter(tenant=request.user)
    else:
        requests = ServiceRequest.objects.filter(
            is_provider_selected=False,
            status='pending'
        )
    return render(request, 'services/request_list.html', {'requests': requests})

@login_required
def service_request_detail(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    
    # Check if user has permission to view this request
    if not (request.user.is_staff or request.user == service_request.tenant or 
            (service_request.provider and request.user == service_request.provider)):
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('services:request_list')

    # Create chat room if service request has a provider
    chat_room = None
    if service_request.provider:
        chat_room, created = ChatRoom.objects.get_or_create(service_request=service_request)
    
    # Get or prepare forms
    offer_form = None
    review_form = None
    
    print(f"User type: {request.user.user_type}")
    print(f"Service request status: {service_request.status}")
    print(f"Is provider selected: {service_request.is_provider_selected}")
    
    if request.user.user_type == 'serviceprovider' and service_request.status == 'pending':
        offer_form = ServiceOfferForm()
    
    if (request.user == service_request.tenant and 
        service_request.status == 'completed' and 
        not hasattr(service_request, 'review')):
        review_form = ServiceReviewForm()
    
    # Get offers if user is tenant or if user is the provider who made the offer
    offers = service_request.offers.all() if request.user == service_request.tenant else \
            service_request.offers.filter(provider=request.user)
    
    context = {
        'service_request': service_request,
        'offer_form': offer_form,
        'review_form': review_form,
        'offers': offers,
        'chat_room': chat_room,
    }
    
    return render(request, 'services/request_detail.html', context)

@login_required
def submit_offer_view(request, service_request_id):
    service_request = get_object_or_404(ServiceRequest, pk=service_request_id)
    offer_form = ServiceOfferForm()
    return render(request, 'services/submit_offer.html', {'offer_form': offer_form, 'service_request': service_request})

@login_required
def submit_offer(request, pk):
    print("\n=== Debug: Submit Offer ===")
    print(f"Request method: {request.method}")
    print(f"User type: {request.user.user_type}")
    print(f"User ID: {request.user.id}")
    print(f"Request path: {request.path}")
    
    if request.user.user_type != 'serviceprovider':
        print("Error: Unauthorized - Not a service provider")
        messages.error(request, 'Unauthorized access.')
        return redirect('services:request_list')

    service_request = get_object_or_404(ServiceRequest, pk=pk)
    print(f"\nService request details:")
    print(f"ID: {service_request.pk}")
    print(f"Status: {service_request.status}")
    print(f"Is provider selected: {service_request.is_provider_selected}")
    
    if request.method == 'POST':
        print("\nPOST Data received:")
        for key, value in request.POST.items():
            if key != 'csrfmiddlewaretoken':  # Don't log the CSRF token
                print(f"{key}: {value}")
            
        form = ServiceOfferForm(request.POST)
        print("\nChecking form validity...")
        if form.is_valid():
            print("Form is valid. Cleaned data:")
            for field, value in form.cleaned_data.items():
                print(f"{field}: {value}")
            
            try:
                offer = form.save(commit=False)
                offer.provider = request.user
                offer.service_request = service_request
                offer.save()
                print("\nOffer saved successfully:")
                print(f"Offer ID: {offer.id}")
                print(f"Provider: {offer.provider.username}")
                print(f"Cost: {offer.proposed_cost}")
                messages.success(request, 'Your offer has been submitted successfully.')
                return redirect('services:request_detail', pk=service_request.pk)
            except Exception as e:
                print(f"\nError saving offer: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                messages.error(request, f'Error saving offer: {str(e)}')
        else:
            print("\nForm validation errors:")
            for field, errors in form.errors.items():
                print(f"{field}: {errors}")
            messages.error(request, f'Invalid form submission. Errors: {form.errors}')
    else:
        print("Not a POST request")
    
    return redirect('services:request_detail', pk=service_request.pk)

@login_required
def accept_offer(request, offer_id):
    offer = get_object_or_404(ServiceOffer, pk=offer_id)
    service_request = offer.service_request
    
    if request.user != service_request.tenant:
        messages.error(request, 'Unauthorized action.')
        return redirect('services:request_list')
    
    service_request.provider = offer.provider
    service_request.status = 'in_progress'
    service_request.is_provider_selected = True
    service_request.save()
    
    # Create chat room after provider selection
    ChatRoom.objects.create(service_request=service_request)
    
    messages.success(request, 'Offer accepted successfully.')
    return redirect('services:request_detail', pk=service_request.pk)

@login_required
def update_request_status(request, pk):
    print(f"Received request to update status for request ID: {pk}")  # Debugging statement

    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if request.user != service_request.provider:
        print("Unauthorized access attempt")  # Debugging statement
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method != 'POST':
        print("Invalid request method")  # Debugging statement
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        print(f"New status received: {new_status}")  # Debugging statement
    except json.JSONDecodeError:
        print("Invalid JSON received")  # Debugging statement
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if new_status in ['in_progress', 'completed']:
        service_request.status = new_status
        if new_status == 'completed':
            service_request.completed_at = timezone.now()
            print("Status updated to completed")  # Debugging statement
        service_request.save()
        print("Service request saved successfully")  # Debugging statement
        return JsonResponse({'status': 'success'})
    
    print("Invalid status received")  # Debugging statement
    return JsonResponse({'error': 'Invalid status'}, status=400)


@login_required
def submit_review(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if request.user != service_request.tenant:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        form = ServiceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.service_request = service_request
            review.save()
            return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def send_message(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if request.method == 'POST':
        form = ServiceMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.service_request = service_request
            message.sender = request.user
            message.save()
            return JsonResponse({
                'status': 'success',
                'message': {
                    'sender': request.user.username,
                    'content': message.message,
                    'timestamp': message.created_at.strftime('%b %d, %Y %H:%M')
                }
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def search_providers(request):
    form = ServiceProviderSearchForm(request.GET)
    providers = ProviderProfile.objects.select_related('user').prefetch_related(
        'categories'
    ).filter(user__user_type='serviceprovider')

    # Calculate average rating for each provider using service requests
    for provider in providers:
        reviews = ServiceReview.objects.filter(
            service_request__provider=provider.user
        ).select_related('service_request')
        
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        total_reviews = reviews.count()
        provider.avg_rating = avg_rating or 0
        provider.total_reviews = total_reviews

    if form.is_valid():
        category = form.cleaned_data.get('category')
        location = form.cleaned_data.get('location')
        rating = form.cleaned_data.get('rating')
        availability = form.cleaned_data.get('availability')

        if category:
            providers = providers.filter(categories=category)
        if location:
            providers = providers.filter(user__provider_profile__service_location__icontains=location)
        if rating:
            # Filter after calculating average ratings
            providers = [p for p in providers if p.avg_rating >= float(rating)]
        if availability:
            providers = providers.filter(is_available=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        provider_list = [{
            'id': p.user.id,
            'name': p.user.get_full_name() or p.user.username,
            'rating': p.avg_rating,
            'total_reviews': p.total_reviews,
            'categories': [c.name for c in p.categories.all()],
            'location': p.user.provider_profile.service_location,
            'is_available': p.is_available
        } for p in providers]
        return JsonResponse({'providers': provider_list})

    context = {
        'form': form,
        'providers': providers
    }
    return render(request, 'services/provider_search.html', context)

@login_required
def provider_profile(request, pk):
    provider = get_object_or_404(CustomUser, pk=pk, user_type='serviceprovider')
    try:
        profile = ProviderProfile.objects.get(user=provider)
    except ProviderProfile.DoesNotExist:
        profile = ProviderProfile.objects.create(user=provider)
    
    reviews = ServiceReview.objects.filter(
        service_request__provider=provider
    ).select_related(
        'reviewer', 'service_request', 'service_request__category'
    ).order_by('-created_at')
    
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    profile.avg_rating = avg_rating
    
    context = {
        'provider': provider,
        'profile': profile,
        'reviews': reviews
    }
    return render(request, 'services/provider_profile.html', context)

@login_required
def provider_dashboard(request):
    if request.user.user_type != 'serviceprovider':
        messages.error(request, 'Unauthorized access')
        return redirect('home')

    upcoming_jobs = ServiceRequest.objects.filter(
        provider=request.user,
        status__in=['assigned', 'in_progress']
    ).order_by('scheduled_date')

    completed_jobs = ServiceRequest.objects.filter(
        provider=request.user,
        status='completed'
    ).order_by('-completed_at')[:5]

    days_of_week = [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday',
        'Friday', 'Saturday', 'Sunday'
    ]

    context = {
        'upcoming_jobs': upcoming_jobs,
        'completed_jobs': completed_jobs,
        'days_of_week': days_of_week
    }
    return render(request, 'services/provider_dashboard.html', context)
