from django.shortcuts import render
from chatapp.models import *
from chatapp.serializers import *
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action

#################################################################################
################################# User View #####################################
#################################################################################

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

    def create(self, request):
        data = request.data

        name = data.get("name")
        if not name:
            return Response({
                "status": False,
                "message": "Name is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email = data.get("email")
        if not email:
            return Response({
                "status": False,
                "message": "Email is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif User.objects.filter(email=email).exists():
            return Response({
                "status": False,
                "message": "Email is already exists",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if '@' in email and email.count('@') == 1:
            email_validate = email.split('@')[1].lower()
        else:
            return Response({
                "status": False,
                "message": "Enter a valid email address",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        password = data.get("password")
        if not password:
            return Response({
                "status": False,
                "message": "Password is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if "is_online" not in data:
            return Response({
                "status": False,
                "message": "is_online Status is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        is_online = data.get("is_online")        
        if is_online not in [True, False]:
            return Response({
                "status": False,
                "message": "is_online allowed_status is True or False",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "User Created Successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "message": serializer.errors,
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        user = request.user
        if not user.is_authenticated:
             return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = self.filter_queryset(self.get_queryset())
        serializer = UserSerializer(user, many=True)
        return Response({
            "status": True,
            "message": "List of Users",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({
                "status": False,
                "message": f"User with id {pk} does not exist",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSerializer(user)
        return Response({
            "status": True,
            "message": "User detail is",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='online')
    def online_users(self, request):
        user = request.user
        if not user.is_authenticated:
             return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        users = User.objects.filter(is_online=True)
        serializer = self.get_serializer(users, many=True)
        return Response({
            "status": True,
            "message": "Online Users are",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

#################################################################################
################################# Log in ########################################
#################################################################################

class LoginViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = LoginSerializer

    def create(self, request):
        data = request.data
        email = data.get("email")
        if not email:
            return Response({
                "status": False,
                "message": "Email is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if '@' in email and email.count('@') == 1:
            email_validate = email.split('@')[1].lower()
        else:
            return Response({
                "status": False,
                "message": "Enter a valid email address",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        password = data.get("password")
        if not password:
            return Response({
                "status": False,
                "message": "Password is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "status": False,
                "message": "User not exists.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not check_password(password, user.password):
            return Response({
                "status": False,
                "message": "Invalid Password",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            "status": True,
            "message": "Login Successful",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }
        }, status=status.HTTP_200_OK)
    
#################################################################################
################################# Log out #######################################
#################################################################################

class LogoutViewSet(APIView):
    def post(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                "status": True,
                "message": "Logout successfully",
                "data": None
            }, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({
                "status": False,
                "message": "Invalid token",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
#################################################################################
################################# Profile #######################################
#################################################################################

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def retrieve(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({
                    "status": False,
                    "message": "Authentication credentials were not provided.",
                    "data": None
                }, status=401)

        if pk != user.id:
            return Response({
                    "status": False,
                    "message": "You are not allowed to access this info.",
                    "data": None
                }, status=401)

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({
                "status": False,
                "message": f"User with id {pk} does not exist",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSerializer(user)
        return Response({
            "status": True,
            "message": "Your detail is",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

#################################################################################
################################# Chat ##########################################
#################################################################################

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def create(self, request):
        data = request.data
        user = request.user

        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        type = data.get("type")
        if not type:
            return Response({
                "status": False,
                "message": "Chat type is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        allowed_chat_types = ["personal", "group"]
        if type not in allowed_chat_types:
            return Response({
                "status": False,
                "message": f"Invalid chat type. Allowed chat type are {allowed_chat_types}",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Chat started successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "message": serializer.errors,
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='messages')
    def get_messages(self, request, pk=None):
        user = request.user

        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            chat = Chat.objects.get(pk=pk)
        except Chat.DoesNotExist:
            return Response({
                "status": False,
                "message": f"Chat with id {pk} does not exist",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not ChatMember.objects.filter(chat_id_id=chat, user_id_id=user).exists():
            return Response({
                "status": False,
                "messages": "You are not a member of this chat.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        
        messages = Message.objects.filter(chat_id_id=chat).order_by("-created_at")
        
        serializer = MessageSerializer(messages, many=True)
        return Response({
            "status": True,
            "message": "Your chat is",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        user = request.user

        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            chat = Chat.objects.get(pk=pk)
        except Chat.DoesNotExist:
            return Response({
                "status": False,
                "message": f"Chat with id {pk} does not exist",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
    
        if not ChatMember.objects.filter(chat_id_id=chat, user_id_id=user).exists():
            return Response({
                "status": False,
                "message": "You are not a member of this chat",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        chat.delete()
        return Response({
            "status": True,
            "message": "Chat deleted successfully",
            "data": None
        }, status=status.HTTP_200_OK)
    
#################################################################################
################################# Group #########################################
#################################################################################

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def create(self, request):
        data = request.data
        user = request.user

        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        name = data.get("name")
        if not name:
            return Response({
                "status": False,
                "message": "Group Name is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(admin=user)
            return Response({
                "status": True,
                "message": "Group created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "message": serializer.errors,
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        user = request.user

        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        group = self.get_object()
        
        if group.admin != user:
            return Response({
                "status": False,
                "message": "Only group admin can add members",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        
        member_id = request.data.get("user_id")

        if not member_id:
            return Response({
                "status": False,
                "message": "user_id is required",
                "data": False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            member = User.objects.get(id=member_id)
        except User.DoesNotExist:
            return Response({
                "status": False,
                "message": "User does not exist",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if ChatMember.objects.filter(group=group, user_id=member).exists():
            return Response({
                "status": False,
                "message": "User already exist",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ChatMember.objects.create(group=group, user_id=member)

        return Response({
            "status": True,
            "message": "Member added successfully",
            "data": {
                "group_id": group.id,
                "user_id": member.id
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        user = request.user

        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)

        group = self.get_object()

        if group.admin != user:
            return Response({
                "status": False,
                "message": "Only group admin can add members",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        
        member_id = request.data.get("user_id")

        if not member_id:
            return Response({
                "status": False,
                "message": "user_id is required",
                "data": False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            member = User.objects.get(id=member_id)
        except User.DoesNotExist:
            return Response({
                "status": False,
                "message": "User does not exist",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if member == group.admin:
            return Response({
                "status": False,
                "message": "Admin cannot remove himself",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        chat_member = ChatMember.objects.filter(group=group, user_id=member)

        if not chat_member.exists():
            return Response({
                "status": False,
                "data": "User is not member of this group",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        chat_member.delete()
        return Response({
            "status": True,
            "message": "Member removed successfully",
            "data": {
                "group_id": group.id,
                "user_id": member.id
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='messages')
    def get_messages(self, request, pk=None):
        user = request.user

        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        group = self.get_object()

        is_member = ChatMember.objects.filter(group=group, user_id=user).exists()
        if not is_member:
            return Response({
                "status": False,
                "message": "You are not a member of this group",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        
        chat_member = ChatMember.objects.filter(group=group).first()
        chat = chat_member.chat_id
        messages = Message.objects.filter(chat_id=chat).order_by('-created_at')

        data = []
        for msg in messages:
            data.append({
                "id": msg.id,
                "sender_id": msg.sender_id.id,
                "message": msg.message,
                "type": msg.type,
                "created_at": msg.created_at,
                "is_read": msg.is_read,
                "is_delivered": msg.is_delivered,
            })

        return Response({
            "status": True,
            "message": "Messages fetched successfully",
            "data": data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        user = request.user

        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            group = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response({
                "status": False,
                "message": "Group not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if group.admin != user:
            return Response({
                "status": False,
                "message": "Only group admin can delete this group",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        group.delete()

        return Response({
            "status": True,
            "message": "Group deleted successfully",
            "data": None
        }, status=status.HTTP_200_OK)