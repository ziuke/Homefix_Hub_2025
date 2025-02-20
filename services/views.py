from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.utils import timezone
from django.http import HttpResponse
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
from ratings.models import ServiceReview, ServiceRequest
from chat.models import ChatRoom
from users.models import CustomUser
from django.contrib.auth.models import User
from django.db.models import Avg
from django.urls import reverse
from .forms import DirectServiceRequestForm
from .models import DirectServiceRequest
from django.conf import settings
from django.core.mail import send_mail
from users.views import tenant_profile
from users.models import TenantProfile
@login_required
def service_request_create(request):
    tenant_profile = TenantProfile.objects.get(user=request.user)  # Get the tenant profile of the logged-in user

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

        # Autofill the location field with the user's tenant profile location
        if 'location' in form.fields:
            form.fields['location'].initial = tenant_profile.location

    return render(request, 'services/request_form.html', {'form': form})

from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def service_request_list(request):
    if request.user.user_type == 'tenant':
        requests = ServiceRequest.objects.filter(tenant=request.user)
    else:
        requests = ServiceRequest.objects.filter(
            is_provider_selected=False,
            status='pending'
        )
    
    # Apply filter if status query parameter is provided
    status_filter = request.GET.get('status', None)
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    # Check if the request is an AJAX request by inspecting the header
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Render only the filtered list of requests
        html = render_to_string('services/request_list_grid.html', {'requests': requests})
        return JsonResponse({'html': html})
    
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
                return redirect('services:request_list')
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
    
    return redirect('services:request_list')

@login_required
def accept_offer(request, offer_id):
    offer = get_object_or_404(ServiceOffer, pk=offer_id)
    service_request = offer.service_request
    
    # Ensure only the tenant can accept an offer
    if request.user != service_request.tenant:
        messages.error(request, 'Unauthorized action.')
        return redirect('services:request_list')
    
    # Assign provider and update service request status
    service_request.provider = offer.provider
    service_request.status = 'in_progress'
    service_request.is_provider_selected = True
    service_request.scheduled_date = offer.proposed_date
    service_request.scheduled_time_slot = offer.proposed_time_slot
    service_request.actual_cost = offer.proposed_cost
    service_request.save()

    # Update the accepted offer's status to 'completed'
    offer.status = 'completed'
    offer.save()

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
        'providers': providers,
        'avg_rating': avg_rating
    }
    return render(request, 'services/provider_search.html', context)
from users.models import ServiceProviderProfile
def provider_profile(request, pk):
    provider = get_object_or_404(CustomUser, pk=pk)  # Get provider
    reviews = ServiceReview.objects.filter(service_request__provider=provider)  # Get reviews
    service_offers = ServiceOffer.objects.filter(provider=provider)  # Get offers made by provider
    providers = ProviderProfile.objects.select_related('user').prefetch_related(
        'categories'
    ).filter(user__user_type='serviceprovider')
    provider_profile = ServiceProviderProfile.objects.select_related('user').prefetch_related('service_provided').get(user=provider)
    # Calculate average rating for each provider using service requests
    for i in providers:
        reviews = ServiceReview.objects.filter(
            service_request__provider=i.user
        ).select_related('service_request')
        
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        total_reviews = reviews.count()
        i.avg_rating = avg_rating or 0
    print(provider_profile)
    return render(request, 'services/provider_profile.html', {
        'provider': provider, 
        'reviews': reviews, 
        'service_offers': service_offers,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'provider_profile': provider_profile
    })

@login_required
def provider_dashboard(request):
    if request.user.user_type != 'serviceprovider':
        messages.error(request, 'Unauthorized access')
        return redirect('home')

    # Get assigned requests
    assigned_requests = ServiceRequest.objects.filter(
        provider=request.user,
        status__in=['assigned', 'in_progress', 'pending']
    ).order_by('scheduled_date')

    # Get upcoming jobs
    upcoming_jobs = ServiceRequest.objects.filter(
        provider=request.user,
        status__in=['assigned', 'in_progress']
    ).order_by('scheduled_date')

    # Get completed jobs
    completed_jobs = ServiceRequest.objects.filter(
        provider=request.user,
        status='completed'
    ).order_by('-completed_at')[:5]
    
    # Generate recent activity
    recent_activity = []
    
    # 1. Recently assigned requests (last 7 days)
    recent_assignments = ServiceRequest.objects.filter(
        provider=request.user,
        status='assigned',
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).order_by('-created_at')[:5]
    
    for service_req in recent_assignments:
        recent_activity.append({
            'title': f"New Job Assignment: {service_req.title}",
            'description': f"You've been assigned to handle {service_req.title} in {service_req.location}",
            'created_at': service_req.created_at,
            'link': reverse('services:request_detail', args=[service_req.id]),
            'type': 'assignment'
        })
    
    # 2. Recent status changes
    recent_status_changes = ServiceRequest.objects.filter(
        provider=request.user,
        status__in=['in_progress', 'completed', 'cancelled']
    ).order_by('-completed_at', '-created_at')[:5]
    
    for service_req in recent_status_changes:
        if service_req.status == 'in_progress':
            action = "started"
            timestamp = service_req.created_at
        elif service_req.status == 'completed':
            action = "completed"
            timestamp = service_req.completed_at or service_req.created_at
        elif service_req.status == 'cancelled':
            action = "cancelled"
            timestamp = service_req.created_at
        
        recent_activity.append({
            'title': f"Status Update: {service_req.title}",
            'description': f"Service request has been {action}",
            'created_at': timestamp,
            'link': reverse('services:request_detail', args=[service_req.id]),
            'type': 'status_update'
        })
    
    # 3. Upcoming scheduled jobs (next 7 days)
    upcoming_scheduled = ServiceRequest.objects.filter(
        provider=request.user,
        status__in=['assigned', 'in_progress'],
        scheduled_date__gte=timezone.now().date(),
        scheduled_date__lte=timezone.now().date() + timezone.timedelta(days=7)
    ).order_by('scheduled_date')[:3]
    
    for service_req in upcoming_scheduled:
        time_info = f" at {service_req.scheduled_time_slot}" if service_req.scheduled_time_slot else ""
        recent_activity.append({
            'title': f"Upcoming Job: {service_req.title}",
            'description': f"Scheduled for {service_req.scheduled_date.strftime('%B %d, %Y')}{time_info}",
            'created_at': service_req.created_at,
            'link': reverse('services:request_detail', args=[service_req.id]),
            'type': 'upcoming'
        })
    
    # 4. Recently completed jobs
    for job in completed_jobs:
        recent_activity.append({
            'title': f"Job Completed: {job.title}",
            'description': f"You completed this service on {job.completed_at.strftime('%B %d, %Y')}",
            'created_at': job.completed_at,
            'link': reverse('services:request_detail', args=[job.id]),
            'type': 'completed'
        })
    
    # Sort all activities by date (newest first) - handle possible None values
    recent_activity.sort(key=lambda x: x['created_at'] if x['created_at'] else timezone.now(), reverse=True)
    recent_activity = recent_activity[:10]  # Limit to 10 most recent activities

    # Get direct service requests (for the logged-in provider)
    direct_requests = DirectServiceRequest.objects.filter(
        provider=request.user
    ).order_by('-created_at')

    days_of_week = [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday',
        'Friday', 'Saturday', 'Sunday'
    ]

    context = {
        'assigned_requests': assigned_requests,
        'upcoming_jobs': upcoming_jobs,
        'completed_jobs': completed_jobs,
        'direct_requests': direct_requests,  # Added direct requests to context
        'days_of_week': days_of_week,
        'recent_activity': recent_activity,
    }
    return render(request, 'services/provider_dashboard.html', context)
@login_required
def direct_service_request_create(request, provider_id):
    # Only allow selecting a service provider
    provider = get_object_or_404(CustomUser, pk=provider_id, user_type='serviceprovider')
    
    if request.method == 'POST':
        form = DirectServiceRequestForm(request.POST)
        if form.is_valid():
            direct_request = form.save(commit=False)
            direct_request.tenant = request.user
            direct_request.provider = provider
            direct_request.save()
            messages.success(request, "Your service request has been sent successfully!")
            return redirect('services:provider_profile', pk=provider.pk)
    else:
        form = DirectServiceRequestForm()
    
    return render(request, 'services/direct_service_request_form.html', {
        'form': form,
        'provider': provider
    })

@login_required
def direct_service_request_list(request):
    # If the user is a service provider, show the requests they've received;
    # otherwise (tenant), show the ones they have sent.
    if request.user.user_type == 'serviceprovider':
        direct_requests = DirectServiceRequest.objects.filter(provider=request.user)
    else:
        direct_requests = DirectServiceRequest.objects.filter(tenant=request.user)
    
    return render(request, 'services/direct_service_request_list.html', {
        'direct_requests': direct_requests
    })

@login_required
def direct_service_request_update(request, pk):
    direct_request = get_object_or_404(DirectServiceRequest, pk=pk)
    
    # Only allow the provider to update the request
    if request.user != direct_request.provider:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if new_status in ['accepted', 'rejected', 'completed']:
            direct_request.status = new_status
            direct_request.save()
            
            # If the status is set to completed, send an email to the tenant.
            if new_status == 'completed':
                subject = "Your Service Request Has Been Completed"
                message = (
                    f"Hello {direct_request.tenant.get_full_name() or direct_request.tenant.username},\n\n"
                    "We are pleased to inform you that your service request has been marked as completed. "
                    "Thank you for using our service!\n\nBest regards,\nYour Service Team"
                )
                from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@example.com'
                recipient_list = [direct_request.tenant.email]
                send_mail(subject, message, from_email, recipient_list)
                # The email will be printed to the terminal in debug mode.

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'error': 'Invalid status'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def direct_service_request_detail(request, pk):
    direct_request = get_object_or_404(DirectServiceRequest, pk=pk)

    # Only the provider should be able to view the request details
    if request.user != direct_request.provider and request.user != direct_request.tenant:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    tenant = direct_request.tenant  # Retrieve the associated tenant object
    return render(request, 'services/direct_service_request_detail.html', {
        'direct_request': direct_request,
        'tenant': tenant  # Pass the tenant object to the template
    })
