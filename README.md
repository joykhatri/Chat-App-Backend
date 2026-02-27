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
