# Chat-App-Backend

The **Chat Application** is a **real-time messaging system** that allows users to **communicate** instantly through text messages **using WebSockets**.

## 🚀 Setup Instructions

### 1️⃣ Create Virtual Environment
```bash
python -m venv .venv
```

### 2️⃣ Activate Virtual Environment
```bash
.venv\Scripts\activate
```

### Linux/macOS:
```bash
source .venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install django djangorestframework mysqlclient
pip install django-filter
pip install djangorestframework-simplejwt     # JWT Authentication
pip install channels                          # WebSocket support
pip install daphne                            # ASGI server for WebSocket
```

### 4️⃣ Start Django Project & App
```bash
django-admin startproject chatproject .
django-admin startapp chatapp
```

### 5️⃣ Add Apps to INSTALLED_APPS (project/settings.py)
```bash
INSTALLED_APPS = [
    ...
    'chatapp',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'channels',
]
```

### 6️⃣ Configure MySQL Database (settings.py)
```bash
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'DB_NAME',
        'USER': 'DB_USER',
        'PASSWORD': 'DB_PASSWORD',
        'HOST': 'localhost',   # Or your DB host
        'PORT': '3306',
    }
}
```

### 7️⃣ Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 8️⃣ Run Server
### Development server:
```bash
python manage.py runserver
```

### ASGI/Daphne server (for WebSocket):
```bash
$env:DJANGO_SETTINGS_MODULE="chatproject.settings"   # Windows PowerShell
daphne -p 8000 chatproject.asgi:application
```

## 🔑 API Endpoints

### Authentication Module
| Method | Endpoint                                            | Description                              |
| ------ | --------------------------------------------------- | ---------------------------------------- |
| POST   | `/api/register/`                                    | User Registration                        |
| POST   | `/api/login/`                                       | User Login                               |
| POST   | `/api/logout/`                                      | User Logout                              |
| GET    | `/api/profile/`                                     | Get Profile info                         |
| GET    | `/api/users/`                                       | Get User List                            |
| GET    | `/api/users/{id}/`                                  | Get User Profile info with Id            |
| GET    | `/api/users/?name=demo`                             | Search Users                             |
| GET    | `/api/users/online/`                                | Get Online Users Info                    |
| POST   | `/api/chat/start/`                                  | Start new Chat                           |
| GET    | `/api/chat/{chat_id}/messages/`                     | All Messages                             |
| DELETE   | `/api/chat/{chat_id}/`                            | Delete Chat                              |


### Register
```bash
{
    "name": "demo",
    "email": "demo@gmail.com",
    "password": "demo@123",
    "is_online": true
}
```

### Login
```bash
{
    "email": "demo@gmail.com",
    "password": "demo@123"
}
```
- Returns access and refresh tokens
```bash
Use access token in Authorization header for protected endpoints:
Authorization: Bearer <access_token>
```

### Logout
```bash
{
    "refresh_token": "Your Refresh Token"
}

- Use access token in Authorization header for protected endpoints:
Authorization: Bearer <access_token>
- Use refresh token in payload for Logout
```

### Start Chat
```bash
{
    "type": "personal"
}
```

## 🌐 WebSocket Endpoints

### For Chat
```bash
ws://127.0.0.1:8000/ws/chat/{chat_id}/?user_id={id}

- Message
{
    "event": "send_message",
    "receiver_id": 2,
    "message": "Hello",
    "type": "text"
}
```
