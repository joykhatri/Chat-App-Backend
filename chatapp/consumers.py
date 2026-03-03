import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import now

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.group_name = f"chat_{self.chat_id}"

        query_params = parse_qs(self.scope["query_string"].decode())
        user_ids = query_params.get("user_id")

        user_id = user_ids[0]
        user = await self.get_user(user_id)
        if not user:
            await self.close()
            return
        
        self.scope["user"] = user
        self.user_id = user.id

        self.user_group_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
        await self.accept()

        await self.mark_user_online(self.user_id)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "user_online",
                "user_id": self.user_id
            }
        )

        message_info = await self.mark_undelivered_message(self.user_id)
        for msg in message_info:
            await self.channel_layer.group_send(
                f"user_{msg['sender_id']}",
                {
                    "type": "message_delivered",
                    "message_id": msg["message_id"]
                }
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data.get("event")

        if event == "send_message":
            chat_id = data.get("chat_id")
            if not chat_id:
                chat_id = await self.create_personal_chat(
                    self.user_id,
                    data["receiver_id"]
                )

            message_obj = await self.save_message(
                chat_id = chat_id,
                receiver_id = data["receiver_id"],
                message_text = data["message"],
                msg_type = data.get("type", "text")
            )

            await self.channel_layer.group_send(
                f"chat_{chat_id}",
                {
                    "type": "receive_message",
                    "message": message_obj
                }
            )

            is_online = await self.is_user_online(data["receiver_id"])
            if is_online:
                await self.mark_message_delivered(message_obj["message_id"])
                await self.channel_layer.group_send(
                    f"user_{self.user_id}",
                    {
                        "type": "message_delivered",
                        "message_id": message_obj["message_id"]
                    }
                )

        elif event == "typing":
            await self.channel_layer.group_send(
                f"chat_{data['chat_id']}",
                {
                    "type": "typing_event",
                    "user_id": self.scope["user"].id,
                    "is_typing": data["is_typing"]
                }
            )  

        elif event == "message_read":
            sender_id = await self.mark_message_read(data["message_id"])
            if sender_id:
                await self.channel_layer.group_send(
                    f"chat_{data['chat_id']}",
                    {
                        "type": "message_read",
                        "message_id": data["message_id"]
                    }
                )

        elif event == "user_offline":
            await self.mark_user_offline(self.user_id)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "user_offline",
                    "user_id": self.user_id
                }
            )

    async def receive_message(self, event):
        await self.send(text_data=json.dumps({
            "event": "receive_message",
            "data": event["message"]
        }))

    async def typing_event(self, event):
        await self.send(text_data=json.dumps({
            "event": "typing",
            "user_id": event["user_id"],
            "is_typing": event["is_typing"]
        }))

    async def message_delivered(self, event):
        await self.send(text_data=json.dumps({
            "event": "message_delivered",
            "message_id": event["message_id"] 
        }))

    async def message_read(self, event):
        await self.send(text_data=json.dumps({
            "event": "message_read",
            "message_id": event["message_id"]
        }))

    async def user_online(self, event):
        await self.send(text_data=json.dumps({
            "event": "user_online",
            "user_id": event["user_id"]
        }))

    async def user_offline(self, event):
        await self.send(text_data=json.dumps({
            "event": "user_offline",
            "user_id": event["user_id"]
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        from chatapp.models import User
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        
    @database_sync_to_async
    def is_user_online(self, user_id):
        from chatapp.models import User
        try:
            return User.objects.get(id=user_id).is_online
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_undelivered_message(self, user_id):
        from chatapp.models import Message

        undelivered_message = Message.objects.filter(
            receiver_id = user_id,
            is_delivered = False
        )
        messages = list(undelivered_message.values("id", "sender_id"))
        undelivered_message.update(is_delivered=True)

        return[
            {
                "message_id": msg["id"],
                "sender_id": msg["sender_id"]
            }
            for msg in messages
        ]

    @database_sync_to_async
    def save_message(self, chat_id, message_text, receiver_id, msg_type="text"):
        from chatapp.models import Message, Chat, User
        from django.utils.timezone import now

        chat = Chat.objects.get(id=chat_id)
        sender = User.objects.get(id=self.user_id)
        receiver = User.objects.get(id=receiver_id)

        msg = Message.objects.create(
            chat_id = chat,
            sender_id = sender,
            receiver_id = receiver,
            message = message_text,
            type = msg_type,
            created_at = now()
        )

        return{
            "message_id": msg.id,
            "sender_id": sender.id,
            "chat_id": chat.id,
            "message": msg.message,
            "timestamp": str(msg.created_at)
        }
    
    @database_sync_to_async
    def create_personal_chat(self, user_id1, user_id2):
        from chatapp.models import Chat, ChatMember

        user1_chats = ChatMember.objects.filter(user_id_id=user_id1).values_list("chat_id_id", flat=True)
        user2_chats = ChatMember.objects.filter(user_id_id=user_id2).values_list("chat_id_id", flat=True)

        chats = set(user1_chats).intersection(set(user2_chats))

        if chats:
            return list(chats)[0]

        chat = Chat.objects.create(type="personal")
        ChatMember.objects.bulk_create([
            ChatMember(chat_id=chat, user_id_id=user_id1),
            ChatMember(chat_id=chat, user_id_id=user_id2)
            ])

        return chat.id

    @database_sync_to_async
    def mark_message_delivered(self, message_id):
        from chatapp.models import Message
        Message.objects.filter(id=message_id).update(is_delivered=True)

    @database_sync_to_async
    def mark_message_read(self, message_id):
        from chatapp.models import Message
        Message.objects.filter(id=message_id).update(is_read=True)

    @database_sync_to_async
    def mark_user_online(self, user_id):
        from chatapp.models import User
        User.objects.filter(id=user_id).update(is_online=True)

    @database_sync_to_async
    def mark_user_offline(self, user_id):
        from chatapp.models import User
        User.objects.filter(id=user_id).update(is_online=False)