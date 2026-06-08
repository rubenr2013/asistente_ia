"""
Configuración de Django para el proyecto ARIA.
Aquí se configura la base de datos, las apps, la seguridad,
y todo lo que Django necesita para funcionar.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Cargamos las variables del archivo .env
# Buscamos primero en la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))


# =============================================
# SEGURIDAD
# =============================================

# Clave secreta — viene del .env (NUNCA ponerla directa en el código)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'clave-por-defecto-solo-para-desarrollo')

# Modo debug — True en desarrollo, False en producción
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Hosts que pueden acceder a la app
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# =============================================
# APPS INSTALADAS
# =============================================

INSTALLED_APPS = [
    # Apps de Django que vienen por defecto
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Para formatear fechas y números bonito

    # Nuestras apps
    'usuarios',   # Login y registro
    'core',       # Chat principal con ARIA
    'correo',     # Gestión de Gmail
    'notas',      # Sistema de notas
    'informes',   # Reportes de actividad
]


# =============================================
# MIDDLEWARE (procesadores de cada petición)
# =============================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Sirve archivos estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'asistente_ia.urls'


# =============================================
# TEMPLATES (páginas HTML)
# =============================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Buscamos templates en la carpeta 'templates' de la raíz
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,  # También busca en templates/ de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'asistente_ia.wsgi.application'


# =============================================
# BASE DE DATOS — PostgreSQL
# =============================================

# Leemos la URL de la base de datos del .env
DATABASE_URL = os.getenv('DATABASE_URL', '')

if DATABASE_URL:
    # Si hay una DATABASE_URL, usamos PostgreSQL
    # La URL tiene formato: postgresql://usuario:password@host:puerto/nombre
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DATABASE_URL.split('/')[-1].split('?')[0],
            'USER': DATABASE_URL.split('://')[1].split(':')[0],
            'PASSWORD': DATABASE_URL.split(':')[2].split('@')[0],
            'HOST': DATABASE_URL.split('@')[1].split(':')[0],
            'PORT': DATABASE_URL.split(':')[-1].split('/')[0],
        }
    }
else:
    # Si no hay URL de PostgreSQL, usamos SQLite para desarrollo rápido
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# =============================================
# VALIDACIÓN DE CONTRASEÑAS
# =============================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =============================================
# IDIOMA Y ZONA HORARIA
# =============================================

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True


# =============================================
# ARCHIVOS ESTÁTICOS (CSS, JavaScript, imágenes)
# =============================================

STATIC_URL = 'static/'

# Carpetas donde Django busca archivos estáticos
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Carpeta donde Django recolecta todos los estáticos para producción
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise comprime y cachea los estáticos en producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# =============================================
# AUTENTICACIÓN
# =============================================

# Si un usuario no está logueado, lo mandamos aquí
LOGIN_URL = '/login/'

# Después de loguearse, lo mandamos al chat
LOGIN_REDIRECT_URL = '/'

# Después de cerrar sesión, lo mandamos al login
LOGOUT_REDIRECT_URL = '/login/'


# =============================================
# CONFIGURACIÓN GENERAL
# =============================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# API Key de Groq para la IA
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
