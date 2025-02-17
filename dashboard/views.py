from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from users.models import CustomUser, TenantProfile, ServiceProviderProfile
from services.models import ServiceRequest, ServiceCategory, ServiceOffer, ServiceReview, ProviderProfile
from .models import ApprovalLog, AdminNotification
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_admin)
def dashboard_home(request):
    # Get counts for different user types
    tenant_count = CustomUser.objects.filter(user_type='tenant').count()
    provider_count = CustomUser.objects.filter(user_type='serviceprovider').count()
    pending_approvals = CustomUser.objects.filter(is_approved=False).exclude(user_type='admin').count()
    
    # Get service-related statistics
    total_requests = ServiceRequest.objects.count()
    active_requests = ServiceRequest.objects.filter(status__in=['pending', 'in_progress']).count()
    completed_requests = ServiceRequest.objects.filter(status='completed').count()
    avg_rating = ServiceReview.objects.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Get recent service requests
    recent_requests = ServiceRequest.objects.select_related('tenant', 'category').order_by('-created_at')[:5]
    
    # Get top-rated providers
    top_providers = ProviderProfile.objects.annotate(
        avg_rating=Avg('user__assigned_requests__servicereview__rating')
    ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:5]
    
    # Get recent registrations (last 7 days)
    recent_registrations = CustomUser.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).exclude(user_type='admin').order_by('-date_joined')[:5]
    
    # Get unread notifications
    notifications = AdminNotification.objects.filter(is_read=False)[:5]
    
    context = {
        'tenant_count': tenant_count,
        'provider_count': provider_count,
        'pending_approvals': pending_approvals,
        'recent_registrations': recent_registrations,
        'notifications': notifications,
        'total_requests': total_requests,
        'active_requests': active_requests,
        'completed_requests': completed_requests,
        'avg_rating': round(avg_rating, 1),
        'recent_requests': recent_requests,
        'top_providers': top_providers,
    }
    return render(request, 'dashboard/home.html', context)

@user_passes_test(is_admin)
def pending_approvals(request):
    pending_users = CustomUser.objects.filter(is_approved=False).exclude(user_type='admin')
    return render(request, 'dashboard/pending_approvals.html', {'pending_users': pending_users})

@user_passes_test(is_admin)
def user_details(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    profile = None
    
    if user.user_type == 'tenant':
        profile = TenantProfile.objects.get(user=user)
    elif user.user_type == 'serviceprovider':
        profile = ServiceProviderProfile.objects.get(user=user)
    
    return render(request, 'dashboard/user_details.html', {
        'user_details': user,
        'profile': profile
    })

@user_passes_test(is_admin)
def approve_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.is_approved = True
        user.is_active = True
        user.save()
        
        # Create approval log
        ApprovalLog.objects.create(
            user=user,
            approved_by=request.user,
            notes=request.POST.get('notes', '')
        )
        
        # Create notification
        AdminNotification.objects.create(
            title=f'User Approved: {user.username}',
            message=f'User {user.username} has been approved by {request.user.username}',
            notification_type='other',
            related_user=user
        )
        
        messages.success(request, f'User {user.username} has been approved successfully.')
        return redirect('dashboard:pending_approvals')
    
    return render(request, 'dashboard/approve_user.html', {'user': user})

@user_passes_test(is_admin)
def reject_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        # Create notification before deletion
        AdminNotification.objects.create(
            title=f'User Rejected: {user.username}',
            message=f'User {user.username} was rejected by {request.user.username}',
            notification_type='other'
        )
        
        user.delete()
        messages.success(request, f'User {user.username} has been rejected and removed from the system.')
        return redirect('dashboard:pending_approvals')
    
    return render(request, 'dashboard/reject_user.html', {'user': user})

@user_passes_test(is_admin)
def user_management(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Filter by user type
    user_type = request.GET.get('user_type')
    if user_type:
        users = users.filter(user_type=user_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        if status == 'active':
            users = users.filter(is_active=True, is_approved=True)
        elif status == 'inactive':
            users = users.filter(is_active=False)
        elif status == 'pending':
            users = users.filter(is_approved=False)
    
    # Search by name, email, or username
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    
    context = {
        'users': users,
        'is_paginated': users.has_other_pages(),
        'page_obj': users,
    }
    return render(request, 'dashboard/user_management.html', context)

@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} has been {status}.')
        
        # Log the status change
        ApprovalLog.objects.create(
            user=user,
            admin=request.user,
            action=f'User {status}',
            notes=f'User status changed to {status}'
        )
        
        return redirect('dashboard:user_management')
    
    return redirect('dashboard:user_management')

@user_passes_test(is_admin)
def notifications(request):
    notifications = AdminNotification.objects.all()
    # Mark all as read
    AdminNotification.objects.filter(is_read=False).update(is_read=True)
    return render(request, 'dashboard/notifications.html', {'notifications': notifications})

@user_passes_test(is_admin)
def approval_logs(request):
    logs = ApprovalLog.objects.all().order_by('-approved_at')
    return render(request, 'dashboard/approval_logs.html', {'logs': logs})

@user_passes_test(is_admin)
def service_categories(request):
    categories = ServiceCategory.objects.annotate(
        request_count=Count('service_requests')
    ).order_by('-request_count')
    
    context = {
        'categories': categories
    }
    return render(request, 'dashboard/service_categories.html', context)

@user_passes_test(is_admin)
def service_requests(request):
    # Adjust the query to use prefetch_related for ManyToManyField
    requests = ServiceRequest.objects.prefetch_related('tenant', 'category').all()

    
    context = {
        'requests': requests
    }
    return render(request, 'dashboard/service_requests.html', context)
@user_passes_test(is_admin)
def request_details(request, request_id):
    # Fetch the service request with related fields
    service_request = get_object_or_404(ServiceRequest.objects.select_related(
        'tenant', 'provider'  # These should be ForeignKey relationships
    ).prefetch_related(
        'category'  # If category is a ManyToManyField, use prefetch_related
    ), id=request_id)

    offers = service_request.offers.select_related('provider').all()
    review = service_request.service_review if hasattr(service_request, 'service_review') else None

    context = {
        'service_request': service_request,
        'offers': offers,
        'review': review
    }
    return render(request, 'dashboard/request_details.html', context)


@user_passes_test(is_admin)
def provider_performance(request):
    providers = ProviderProfile.objects.annotate(
        total_requests=Count('user__assigned_requests', distinct=True),
        completed_requests=Count(
            'user__assigned_requests',
            filter=Q(user__assigned_requests__status='completed'),
            distinct=True
        ),
        avg_rating=Avg('user__assigned_requests__servicereview__rating')
    ).select_related('user').order_by('-avg_rating')
    
    context = {
        'providers': providers
    }
    return render(request, 'dashboard/provider_performance.html', context)

@user_passes_test(is_admin)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        
        category = ServiceCategory.objects.create(
            name=name,
            description=''  # Set a default empty description
        )
        
        messages.success(request, f'Category "{name}" has been created successfully.')
        return redirect('dashboard:service_categories')
    
    return redirect('dashboard:service_categories')

@user_passes_test(is_admin)
def update_category(request, category_id):
    category = get_object_or_404(ServiceCategory, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        category.name = name
        category.save()
        
        messages.success(request, f'Category "{name}" has been updated successfully.')
        return redirect('dashboard:service_categories')
    
    return redirect('dashboard:service_categories')

@user_passes_test(is_admin)
def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(ServiceCategory, id=category_id)
        name = category.name
        category.delete()
        
        messages.success(request, f'Category "{name}" has been deleted successfully.')
        return redirect('dashboard:service_categories')
    
    return render(request, 'dashboard/delete_category.html', {'category_id': category_id})
