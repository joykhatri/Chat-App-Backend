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
    

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def create(self, request):
        data = request.data
        user = request.user

        if not user or not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication credentials were not provided.",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED)

        chat_id = data.get("chat_id")
        if not chat_id:
            return Response({
                "status": False,
                "message": "chat_id field is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        message = data.get("message")
        if not message:
            return Response({
                "status": False,
                "message": "Message field is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        type = data.get("type")
        if not type:
            return Response({
                "status": False,
                "message": "Message type is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        allowed_message_types = ["text", "image", "video", "file"]
        if type not in allowed_message_types:
            return Response({
                "status": False,
                "message": f"Invalid message type. Allowed message type are {allowed_message_types}",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({
                "status": False,
                "message": "Chat does not exist.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        if ChatMember.objects.filter(chat=chat, user=user).exists():
            return Response({
                "status": False,
                "message": "You are not a member of this chat.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Message send successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "message": serializer.errors,
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)