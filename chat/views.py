from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.utils import timezone
from django.contrib import messages
from .models import UserProfile, ChatRoom, Message, GuestUser
import json
import logging

logger = logging.getLogger(__name__)

def home(request):
    """Home page view"""
    return render(request, 'home.html')

@csrf_exempt
def guest_login(request):
    """Handle guest user login"""
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                guest_name = data.get('name')
                emoji = data.get('emoji', '😊')
                preferences = data.get('preferences', '')
                about = data.get('about', '')
            else:
                guest_name = request.POST.get('name')
                emoji = request.POST.get('emoji', '😊')
                preferences = request.POST.get('preferences', '')
                about = request.POST.get('about', '')
            
            if not guest_name:
                return JsonResponse({'success': False, 'error': 'Please enter your name'}, status=400)
            
            # Clear any existing guest user data
            if 'guest_id' in request.session:
                try:
                    old_guest = GuestUser.objects.get(id=request.session['guest_id'])
                    old_guest.delete()
                except GuestUser.DoesNotExist:
                    pass
                del request.session['guest_id']
            
            # Generate a new session key
            request.session.cycle_key()
            
            # Create new guest user with the new session key
            guest = GuestUser.objects.create(
                name=guest_name,
                emoji=emoji,
                preferences=preferences,
                about=about,
                session_key=request.session.session_key
            )
            
            request.session['guest_id'] = guest.id
            return JsonResponse({
                'success': True,
                'redirect': '/chat-select/',
                'guest_id': guest.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error in guest_login: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while processing your request'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember') == 'on'
        
        try:
            user = get_user_model().objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                login(request, user)
                if not remember:
                    request.session.set_expiry(0)
                return JsonResponse({'success': True, 'redirect': '/chat-select/'})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid email or password'})
        except get_user_model().DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No account found with this email'})
    
    return redirect('chat:home')

def logout_view(request):
    """Handle user logout"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
    return redirect('chat:home')

@login_required
def video_chat(request):
    """Video chat view"""
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    return render(request, 'video_chat.html', {'user_profile': user_profile})

@login_required
def text_chat(request):
    """Text chat view"""
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    return render(request, 'text_chat.html', {'user_profile': user_profile})

def chat_select(request):
    """Chat selection view after guest login or user authentication"""
    # Check if user is authenticated or has a guest session
    if not request.user.is_authenticated and 'guest_id' not in request.session:
        return redirect('chat:home')
    
    context = {}
    if 'guest_id' in request.session:
        try:
            guest = GuestUser.objects.get(id=request.session['guest_id'])
            context['guest'] = guest
        except GuestUser.DoesNotExist:
            # If guest user doesn't exist, clear session and redirect to home
            del request.session['guest_id']
            return redirect('chat:home')
    
    return render(request, 'chat_select.html', context)

@login_required
def get_online_users(request):
    """Get list of online users"""
    users = UserProfile.objects.filter(
        is_online=True,
        last_activity__gte=timezone.now() - timezone.timedelta(minutes=5)
    ).exclude(user=request.user)
    
    user_list = [{
        'id': profile.user.id,
        'username': profile.user.username,
        'emoji': profile.emoji,
        'preferences': profile.preferences
    } for profile in users]
    
    return JsonResponse({'users': user_list})

@login_required
def get_chat_history(request, user_id):
    """Get chat history with a specific user"""
    try:
        other_user = get_user_model().objects.get(id=user_id)
        chat_room = ChatRoom.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        if chat_room:
            messages = Message.objects.filter(chat_room=chat_room).order_by('timestamp')
            message_list = [{
                'sender': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'type': msg.message_type
            } for msg in messages]
            
            return JsonResponse({'messages': message_list})
        
        return JsonResponse({'messages': []})
    
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@csrf_exempt
@login_required
def upload_file(request):
    """Handle file uploads in chat"""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        chat_room_id = request.POST.get('chat_room_id')
        
        try:
            chat_room = ChatRoom.objects.get(id=chat_room_id)
            message = Message.objects.create(
                chat_room=chat_room,
                sender=request.user,
                file=file,
                message_type='file' if file.content_type != 'image' else 'image'
            )
            
            return JsonResponse({
                'success': True,
                'file_url': message.file.url,
                'message_id': message.id
            })
            
        except ChatRoom.DoesNotExist:
            return JsonResponse({'error': 'Chat room not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def profile(request):
    """User profile view"""
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    
    if request.method == 'POST':
        user_profile.emoji = request.POST.get('emoji', '')
        user_profile.preferences = request.POST.get('preferences', '')
        user_profile.about = request.POST.get('about', '')
        user_profile.save()
        
        return redirect('profile')
    
    return render(request, 'profile.html', {'user_profile': user_profile})
