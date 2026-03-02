from rest_framework import serializers
from chatapp.models import *
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'is_online', 'last_seen']
        extra_kwargs = {'password' : {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.password = make_password(validated_data['password'])
            validated_data.pop('password')
        return super().update(instance, validated_data)
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'chat_id', 'sender_id', 'message', 'type', 'created_at', 'is_read', 'is_delivered', 'is_deleted']

class ChatMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model : ChatMember
        fields = "__all__"

class ChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    chat_member = ChatMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = "__all__"