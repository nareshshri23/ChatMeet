import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import UserProfile, ChatRoom, Message, GuestUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_group_name = "chat"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        if self.user.is_authenticated:
            await self.update_user_status(True)
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        if self.user.is_authenticated:
            await self.update_user_status(False)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', '')
        
        if message_type == 'message':
            await self.handle_chat_message(data)
        elif message_type == 'typing':
            await self.handle_typing_status(data)
    
    async def handle_chat_message(self, data):
        message = data.get('message', '')
        recipient_id = data.get('recipient')
        
        if message and recipient_id:
            # Save message to database
            chat_room = await self.get_or_create_chat_room(recipient_id)
            await self.save_message(chat_room.id, message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.user.id,
                    'recipient_id': recipient_id
                }
            )
    
    async def handle_typing_status(self, data):
        recipient_id = data.get('recipient')
        is_typing = data.get('typing', False)
        
        if recipient_id:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'recipient_id': recipient_id,
                    'typing': is_typing
                }
            )
    
    async def chat_message(self, event):
        # Send message to WebSocket
        if self.user.id in [event['sender_id'], event['recipient_id']]:
            await self.send(text_data=json.dumps({
                'type': 'new_message',
                'message': event['message'],
                'sender_id': event['sender_id']
            }))
    
    async def user_typing(self, event):
        # Send typing status to WebSocket
        if self.user.id == event['recipient_id']:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'typing': event['typing']
            }))
    
    @database_sync_to_async
    def update_user_status(self, is_online):
        UserProfile.objects.filter(user=self.user).update(
            is_online=is_online,
            last_activity=timezone.now()
        )
    
    @database_sync_to_async
    def get_or_create_chat_room(self, recipient_id):
        chat_room, _ = ChatRoom.objects.get_or_create(
            participants__in=[self.user.id, recipient_id]
        )
        chat_room.participants.add(self.user.id, recipient_id)
        return chat_room
    
    @database_sync_to_async
    def save_message(self, room_id, content):
        Message.objects.create(
            chat_room_id=room_id,
            sender=self.user,
            content=content
        )

class VideoChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_group_name = "video_chat"
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        if self.user.is_authenticated:
            await self.update_user_status(True)
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        if self.user.is_authenticated:
            await self.update_user_status(False)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', '')
        
        if message_type in ['offer', 'answer', 'ice-candidate']:
            await self.handle_webrtc_signal(data)
    
    async def handle_webrtc_signal(self, data):
        target_id = data.get('target')
        
        if target_id:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_signal',
                    'signal_type': data['type'],
                    'signal_data': data.get('data'),
                    'sender_id': self.user.id,
                    'target_id': target_id
                }
            )
    
    async def webrtc_signal(self, event):
        if self.user.id == event['target_id']:
            await self.send(text_data=json.dumps({
                'type': event['signal_type'],
                'data': event['signal_data'],
                'sender_id': event['sender_id']
            }))
    
    @database_sync_to_async
    def update_user_status(self, is_online):
        UserProfile.objects.filter(user=self.user).update(
            is_online=is_online,
            last_activity=timezone.now()
        )
