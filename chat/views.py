from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import ChatRoom, Message
from services.models import ServiceRequest
import json
from .models import Notification    
# Create your views here.

@login_required
def chat_room(request, service_request_id):
    service_request = get_object_or_404(ServiceRequest, id=service_request_id)
    
    # Check if user has access to this chat
    if request.user not in [service_request.tenant, service_request.provider]:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get or create chat room
    chat_room, created = ChatRoom.objects.get_or_create(service_request=service_request)
    
    context = {
        'chat_room': chat_room,
        'service_request': service_request,
        'current_user': request.user
    }
    return render(request, 'chat/chat_room.html', context)

@login_required
def get_messages(request, chat_room_id):
    chat_room = get_object_or_404(ChatRoom, id=chat_room_id)
    
    # Check if user has permission to view messages
    if not (request.user == chat_room.service_request.tenant or 
            request.user == chat_room.service_request.provider):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    messages = Message.objects.filter(chat_room=chat_room).order_by('created_at')
    messages_data = [{
        'id': message.id,
        'content': message.content,
        'sender_id': message.sender.id,
        'sender_name': message.sender.get_full_name() or message.sender.username,
        'created_at': message.created_at.isoformat()
    } for message in messages]
    
    return JsonResponse(messages_data, safe=False)

@login_required
def send_message(request, chat_room_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    chat_room = get_object_or_404(ChatRoom, id=chat_room_id)
    
    # Check if user has permission to send messages
    if not (request.user == chat_room.service_request.tenant or 
            request.user == chat_room.service_request.provider):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': 'Message content is required'}, status=400)
        
        message = Message.objects.create(
            chat_room=chat_room,
            sender=request.user,
            content=content
        )
        
        return JsonResponse({
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender.id,
            'sender_name': message.sender.get_full_name() or message.sender.username,
            'created_at': message.created_at.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def notification_center(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Fetch unread chat messages
    chat_rooms = ChatRoom.objects.filter(participants=request.user)  # Adjust based on your chat model
    unread_messages = []
    
    for room in chat_rooms:
        messages = Message.objects.filter(chat_room=room, is_read=False)  # Adjust based on your message model
        if messages.exists():
            unread_messages.append({
                'room': room,
                'count': messages.count()
            })
    
    return render(request, 'chat/notification_center.html', {
        'notifications': notifications,
        'unread_messages': unread_messages,
    })