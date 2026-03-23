import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import now
from datetime import datetime

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
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data.get("event")

        if event == "send_message":
            chat_id = self.chat_id

            if not chat_id:
                chat_id = await self.create_personal_chat(
                    self.user_id,
                    data["receiver_id"]
                )

            receiver_ids = await self.get_chat_receivers(chat_id)

            message_obj = await self.save_message(
                chat_id = chat_id,
                receiver_ids = receiver_ids,
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

            await self.channel_layer.group_send(
                f"user_{self.user_id}",
                {
                    "type": "new_message"
                }
            )

            for receiver_id in receiver_ids:
                await self.channel_layer.group_send(
                    f"user_{receiver_id}",
                    {
                        "type": "new_message"
                    }
                )

            for receiver_id in receiver_ids:
                is_online = await self.is_user_online(receiver_id)
                if is_online:
                    await self.mark_message_delivered(message_obj["message_id"])
                    await self.channel_layer.group_send(
                        f"user_{receiver_id}",
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
    def save_message(self, chat_id, receiver_ids, message_text, msg_type="text"):
        from chatapp.models import Message, Chat, User
        from django.utils.timezone import now
        
        chat = Chat.objects.get(id=chat_id)
        sender = User.objects.get(id=self.user_id)

        messages = []
        for receiver_id in receiver_ids:
            receiver = User.objects.get(id=receiver_id)

            msg = Message.objects.create(
                chat_id = chat,
                sender_id = sender,
                receiver_id = receiver,
                message = message_text,
                type = msg_type,
                created_at = now()
            )

            messages.append({
                "message_id": msg.id,
                "sender_id": sender.id,
                "receiver_id": receiver_id,
                "chat_id": chat.id,
                "message": msg.message,
                "timestamp": str(msg.created_at)
            })
        return messages[0] if messages else None

    @database_sync_to_async
    def create_personal_chat(self, user_id1, user_id2):
        from chatapp.models import Chat, ChatMember

        user1_chats = ChatMember.objects.filter(user_id_id=user_id1).values_list("chat_id_id", flat=True)
        user2_chats = ChatMember.objects.filter(user_id_id=user_id2).values_list("chat_id_id", flat=True)

        chats = set(user1_chats).intersection(set(user2_chats))

        for chat_id in chats:
            chat = Chat.objects.get(id=chat_id)
            if chat.type == "personal":
                return chat.id

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

    @database_sync_to_async
    def get_chat_receivers(self, chat_id):
        from chatapp.models import ChatMember
        members = ChatMember.objects.filter(chat_id_id=chat_id).exclude(user_id_id=self.user_id)
        return[member.user_id_id for member in members]


class HomeScreenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_params = self.scope["query_string"].decode()
        params = dict(q.split("=") for q in query_params.split("&"))
        self.user_id = int(params.get("user_id"))

        self.user_group_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        # chat_ids = await self.get_user_chat_ids(self.user_id)
        # for chat_id in chat_ids:
        #     await self.channel_layer.group_add(f"chat_{chat_id}", self.channel_name)

        await self.accept()

        # await self.mark_user_online(self.user_id)

        chats = await self.get_user_chats(self.user_id)
        await self.send(text_data=json.dumps({
            "event": "home_screen",
            "data": chats
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        # await self.mark_user_offline(self.user_id)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data.get("event")

        if event == "message_read":
            await self.mark_message_read(data["message_id"])
            await self.send(text_data=json.dumps({
                "event": "message_read",
                "message_id": data["message_id"]
            }))

    # async def receive_message(self, event):
    #     await self.send(text_data=json.dumps({
    #         "event": "receive_message",
    #         "data": event["message"]
    #     }))

    # async def message_delivered(self, event):
    #     await self.send(text_data=json.dumps({
    #         "event": "message_delivered",
    #         "message_id": event["message_id"]
    #     }))

    async def message_delivered(self, event):
        pass

    async def new_chat(self, event):
        chats = await self.get_user_chats(self.user_id)
        await self.send(text_data=json.dumps({
            "event": "home_screen",
            "data": chats
        }))

    async def member_added(self, event):
        chats = await self.get_user_chats(self.user_id)

        await self.send(text_data=json.dumps({
            "event": "home_screen",
            "data": chats
        }))
        # await self.send(text_data=json.dumps({
        #     "event": "member_added",
        #     "message": f"{event['user_name']} joined the group",
        #     "chat_id": event["chat_id"]
        # }))

    async def added_to_group(self, event):
        chats = await self.get_user_chats(self.user_id)

        await self.send(text_data=json.dumps({
            "event": "home_screen",
            "data": chats
        }))
    #     await self.send(text_data=json.dumps({
    #         "event": "added_to_group",
    #         "message": f"You were added to group",
    #         "chat_id": event["chat_id"]
    #     }))

    async def member_removed(self, event):
        chats = await self.get_user_chats(self.user_id)

        await self.send(text_data=json.dumps({
            "event": "home_screen",
            "data": chats
        }))
        # await self.send(text_data=json.dumps({
        #     "event": "member_removed",
        #     "message": f"{event['user_name']} left the group",
        #     "chat_id": event["chat_id"]
        # }))

    async def removed_from_group(self, event):
        chats = await self.get_user_chats(self.user_id)

        await self.send(text_data=json.dumps({
            "event": "home_screen",
            "data": chats
        }))
    #     await self.send(text_data=json.dumps({
    #         "event": "removed_from_group",
    #         "message": "You were removed from group",
    #         "chat_id": event["chat_id"]
    #     }))

    async def new_message(self, event):
        chats = await self.get_user_chats(self.user_id)
        await self.send(text_data=json.dumps({
            "event": "home_screen",
            "data": chats
        }))

    async def group_deleted(self, event):
        chats = await self.get_user_chats(self.user_id)

        await self.send(text_data=json.dumps({
            "event": "home_screen",
            "data": chats
        }))
        # await self.send(text_data=json.dumps({
        #     "event": "group_deleted",
        #     "chat_id": event["chat_id"]
        # }))

    # async def user_online(self, event):
    #     await self.send(text_data=json.dumps({
    #         "event": "user_online",
    #         "data": event["user_id"]
    #     }))

    async def user_online(self, event):
        pass

    async def user_offline(self, event):
        pass

    # async def user_offline(self, event):
    #     await self.send(text_data=json.dumps({
    #         "event": "user_offline",
    #         "data": event["user_id"]
    #     }))

    @database_sync_to_async
    def get_user_chat_ids(self, user_id):
        from chatapp.models import ChatMember
        return list(ChatMember.objects.filter(user_id_id=user_id).values_list("chat_id_id", flat=True))

    @database_sync_to_async
    def get_user_chats(self, user_id):
        from chatapp.models import ChatMember, Message, User

        chat_ids = ChatMember.objects.filter(user_id_id=user_id).values_list('chat_id_id', flat=True)
        chat_data = []

        for chat_id in chat_ids:
            last_msg = Message.objects.select_related("sender_id").filter(chat_id_id=chat_id).order_by('-created_at').first()
            if last_msg:
                # other_members = ChatMember.objects.filter(chat_id_id=chat_id).exclude(user_id_id=user_id)
                # member_info = []
                # for m in other_members:
                #     user = User.objects.get(id=m.user_id_id)
                #     member_info.append({
                #         "id": user.id,
                #         "user": user.name,
                #         "is_online": user.is_online
                #     })

                unread_messages = Message.objects.filter(chat_id_id=chat_id, receiver_id_id=user_id, is_read=False).count()

                chat_data.append({
                    "chat_id": chat_id,
                    "name": last_msg.sender_id.name,
                    "last_message": last_msg.message,
                    "unread_messages": unread_messages,
                    "timestamp": str(last_msg.created_at),
                    # "senders": member_info,
                })
            else:
                chat_data.append({
                "chat_id": chat_id,
                "last_message": None,
                "unread_messages": 0,
                "timestamp": None,
            })
        chat_data.sort(
            key=lambda x: x["timestamp"] or datetime.min,
            reverse=True
        )
        return chat_data
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        from chatapp.models import Message
        Message.objects.filter(id=message_id).update(is_read=True)

    # @database_sync_to_async
    # def mark_user_online(self, user_id):
    #     from chatapp.models import User
    #     User.objects.filter(id=user_id).update(is_online=True)

    # @database_sync_to_async
    # def mark_user_offline(self, user_id):
    #     from chatapp.models import User
    #     User.objects.filter(id=user_id).update(is_online=False)
