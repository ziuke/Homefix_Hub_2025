from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from .forms import TenantRegistrationForm, ServiceProviderRegistrationForm, CustomPasswordResetForm
from .models import CustomUser
from services.models import ServiceRequest, ProviderProfile

def home(request):
    context = {}
    if request.user.is_authenticated:
        if request.user.user_type == 'tenant':
            # Get recent service requests for tenant
            recent_requests = ServiceRequest.objects.filter(
                tenant=request.user
            ).order_by('-created_at')[:4]
            context['recent_requests'] = recent_requests
            
        elif request.user.user_type == 'serviceprovider':
            # Get upcoming jobs for service provider
            upcoming_jobs = ServiceRequest.objects.filter(
                offers__provider=request.user,
                offers__status='accepted',
                status__in=['assigned', 'in_progress']
            ).order_by('scheduled_date')[:4]
            context['upcoming_jobs'] = upcoming_jobs
            
    return render(request, 'users/home.html', context)

def register_tenant(request):
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
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
            user = form.save()
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
        user.save()
        messages.success(request, 'Your email has been verified. You can now log in.')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
    
    return redirect('login')

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
        user.save()
        messages.success(request, f'User {user.username} has been approved.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admin_dashboard')
