from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.http import HttpResponse
from .forms import TenantRegistrationForm, ServiceProviderRegistrationForm, CustomPasswordResetForm
from .models import CustomUser
from services.models import ServiceRequest, ProviderProfile, ServiceReview, ServiceCategory
from .forms import TenantProfileForm, ServiceProviderProfileForm
from .models import TenantProfile, ServiceProviderProfile
from django.contrib.auth.models import User
from services.models import DirectServiceRequest
def home(request):
    context = {}
    
    if request.user.is_authenticated:
        print(f"User: {request.user}, Type: {request.user.user_type}")  # Debug user info

        if request.user.user_type == 'tenant':
            # Get recent service requests for tenant
            recent_requests = ServiceRequest.objects.filter(
                tenant=request.user
            ).order_by('-created_at')[:4]
            context['recent_requests'] = recent_requests

            # Get direct service requests made by the tenant
            tenant_direct_requests = DirectServiceRequest.objects.filter(
                tenant=request.user
            ).order_by('-created_at')[:4]
            
            print(f"Direct Requests for {request.user}: {tenant_direct_requests}")  # Debug output
            context['tenant_direct_requests'] = tenant_direct_requests

        elif request.user.user_type == 'serviceprovider':
            # Get upcoming jobs for service provider
            upcoming_jobs = ServiceRequest.objects.filter(
                offers__provider=request.user,
                offers__status='accepted',
                status__in=['assigned', 'in_progress']
            ).order_by('scheduled_date')[:4]
            context['upcoming_jobs'] = upcoming_jobs

            # Get direct service requests assigned to the provider
            direct_requests = DirectServiceRequest.objects.filter(
                provider=request.user
            ).order_by('-created_at')[:4]
            context['direct_requests'] = direct_requests

    return render(request, 'users/home.html', context)

def register_tenant(request):
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_verification_email(request, user)
            messages.success(request, 'Registration successful. Please check your email to verify your account.')
            return redirect('login')
    else:
        form = TenantRegistrationForm()
    return render(request, 'users/register_tenant.html', {'form': form})

def register_service_provider(request):
    if request.method == 'POST':
        form = ServiceProviderRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            # Create provider profile
            provider_profile = ProviderProfile.objects.create(
                user=user,
                rating=0.0,
                total_reviews=0,
                is_available=True,
                availability={}
            )
            # Add selected categories
            categories = form.cleaned_data.get('categories', [])
            provider_profile.categories.set(categories)
            
            send_verification_email(request, user)
            messages.success(request, 'Registration successful. Please check your email to verify your account.')
            return redirect('login')
    else:
        form = ServiceProviderRegistrationForm()
    return render(request, 'users/register_service_provider.html', {'form': form})

def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_url = request.build_absolute_uri(
        reverse('verify_email', args=[uid, token])
    )
    
    # For development, print the verification link in terminal
    print(f"Verification link: {verification_url}")
    
    subject = 'Verify your email address'
    message = render_to_string('users/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    
    send_mail(subject, message, 'noreply@homefix.com', [user.email])

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.is_active = False
        user.save()
        messages.success(request, 'Your email has been verified. You can now log in.')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
    
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_email_verified != 1:
                return HttpResponse('Email verification required. Please verify your email to log in.')
            login(request, user)
            return redirect('dashboard:home')
    return render(request, 'users/login.html')

@login_required
def profile(request):
    user = request.user
    if user.user_type == 'tenant':
        template = 'users/tenant_profile.html'
        profile = user.tenant_profile
    elif user.user_type == 'serviceprovider':
        template = 'users/service_provider_profile.html'
        profile = user.provider_profile
    else:
        template = 'users/admin_profile.html'
        profile = None
    
    return render(request, template, {'profile': profile})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    pending_users = CustomUser.objects.filter(is_approved=False).exclude(user_type='admin')
    return render(request, 'users/admin_dashboard.html', {'pending_users': pending_users})

@login_required
def approve_user(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_approved = True
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} has been approved.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admin_dashboard')


from django.shortcuts import get_object_or_404
from users.models import CustomUser

@login_required
def edit_profile(request):
    """Allows users to update their profile based on their role (Tenant/Service Provider)."""

    user = get_object_or_404(CustomUser, pk=request.user.pk)  # Ensure the user is a CustomUser instance

    if hasattr(user, 'tenant_profile'):
        profile = user.tenant_profile
        form_class = TenantProfileForm
    elif hasattr(user, 'provider_profile'):
        profile = user.provider_profile
        form_class = ServiceProviderProfileForm
    else:
        messages.error(request, "Profile not found.")
        return redirect('dashboard')  # Redirect to a suitable page

    if request.method == 'POST':
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('tenant_profile' if hasattr(user, 'tenant_profile') else 'provider_profile')

    else:
        form = form_class(instance=profile)

    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def tenant_profile_view(request):
    profile = request.user.tenant_profile
    return render(request, 'users/tenant_profile.html', {'profile': profile})

@login_required
def provider_profile_view(request):
    # Ensure request.user is a CustomUser instance
    if not isinstance(request.user, CustomUser):
        messages.error(request, "Invalid user instance.")
        return redirect('home')

    # Ensure the user has a provider_profile
    profile = getattr(request.user, 'provider_profile', None)
    if not profile:
        messages.error(request, "No provider profile found.")
        return redirect('dashboard')  # Redirect to a relevant page

    # Fetch the services the provider offers
    service_provided = profile.service_provided.all()  # This is more efficient than filtering manually

    # Fetch reviews for the provider
    reviews = ServiceReview.objects.filter(service_request__provider=request.user)

    return render(request, 'services/provider_profile.html', {
        'profile': profile,
        'reviews': reviews,
        'service_provided': service_provided
    })

def generate_reset_link(request):
    if request.method == "POST":
        request_id = json.loads(request.body).get("request_id")
        reset_link = request.build_absolute_uri(reverse('services:request_detail', args=[request_id]))
        
        # Print the reset link to the terminal
        print(f"Generated Reset Link: {reset_link}")

        return JsonResponse({"status": "success", "reset_link": reset_link})
    
    return JsonResponse({"status": "error"}, status=400)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from services.models import ServiceRequest, DirectServiceRequest

@login_required
def client_dashboard(request):
    if request.user.user_type != 'tenant':
        messages.error(request, "Access denied. Only tenants can access this page.")
        return redirect('home')

    # Fetch recent service requests for the logged-in tenant
    recent_requests = ServiceRequest.objects.filter(
        tenant=request.user
    ).order_by('-created_at').select_related('provider')  # No 'service'

    # Fetch direct service requests made by the tenant
    direct_requests = DirectServiceRequest.objects.filter(
        tenant=request.user
    ).order_by('-created_at').select_related('provider')

    context = {
        'recent_requests': recent_requests,
        'direct_requests': direct_requests,
    }

    return render(request, 'users/client_dashboard.html', context)
@login_required
def tenant_profile(request, pk):
    # Only allow service providers to view tenant profiles
    if request.user.user_type != 'serviceprovider':
        return HttpResponseForbidden("You are not authorized to view this page.")
    
    # Get the tenant user with the given pk
    tenant = get_object_or_404(CustomUser, pk=pk, user_type='tenant')
    
    # Try to get the associated TenantProfile
    try:
        tenant_profile = tenant.tenant_profile
    except TenantProfile.DoesNotExist:
        tenant_profile = None

    return render(request, 'users/tenant_public_profile.html', {
        'tenant': tenant,
        'tenant_profile': tenant_profile
    })
