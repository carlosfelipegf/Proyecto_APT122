from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-sbd#^wxmisc$n+(j#s!xy7g_#r2(9d*73dx2n8vg30vz=59#lb'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    # ... aplicaciones de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios.apps.UsuariosConfig',
    
    # Tus apps
    # 'otra_app',
    
    #  SOLUCIÓN: LIBRERÍAS CRISPY FORMS 
    # 1. App base de Crispy Forms
    'crispy_forms', 
    # 2. El paquete de templates específico para Bootstrap 5 (¡NECESARIO!)
    'crispy_bootstrap5', 
]

# Configuración para Django Crispy Forms (usando Bootstrap 5)
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5" # Esto funciona porque ahora tenemos 'crispy_bootstrap5' en INSTALLED_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'OptifireAPT.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'usuarios.context_processors.notificaciones_usuario',
            ],
        },
    },
]


WSGI_APPLICATION = 'OptifireAPT.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        # CAMBIO 1: Aumentamos el mínimo a 10 caracteres
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    # CAMBIO 2: Agregamos nuestro validador personalizado
    {
        'NAME': 'usuarios.validators.ValidarComplejidad',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# OptifireAPT/settings.py (Fragmento)

# URL a donde redirigir si se necesita iniciar sesión
LOGIN_URL = 'login' # Usa el nombre de la ruta de login de Django (que viene en include('django.contrib.auth.urls'))

# URL por defecto a donde redirigir después de iniciar sesión.
# Django buscará esta URL después de un login exitoso.
LOGIN_REDIRECT_URL = '/usuarios/' # Redirige a la nueva vista del inspector/usuario normal

# URL a donde redirigir después de cerrar sesión
LOGOUT_REDIRECT_URL = '/'

# Configuración de Archivos Multimedia (Fotos de perfil, documentos, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -------------------------------------------------------------
# CONFIGURACIÓN DE CORREO ELECTRÓNICO (Para Desarrollo)
# -------------------------------------------------------------

# Esto hace que todos los correos se impriman en la consola (terminal)
# en lugar de ser enviados realmente. Ideal para pruebas.
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' 

# Esta dirección se usa como remitente en la función send_mail
# La pusimos en signals.py, así que debe estar aquí.
#DEFAULT_FROM_EMAIL = 'Optifire <notificaciones@optifire.cl>'

# -------------------------------------------------------------
# CONFIGURACIÓN DE CORREO ELECTRÓNICO (PRODUCCIÓN/REAL)
# -------------------------------------------------------------

#  CAMBIO CLAVE: Cambiamos de 'console' a 'smtp' para enviar correos reales
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' 

# Configuración del servidor (Estándar para Gmail/Outlook)
EMAIL_HOST = 'smtp.gmail.com'  # Servidor SMTP de Google
EMAIL_PORT = 587
EMAIL_USE_TLS = True          # Usar seguridad TLS

# CREDENCIALES (DEBES REEMPLAZAR ESTAS LÍNEAS)
# IMPORTANTE: Reemplaza con tus datos reales
EMAIL_HOST_USER = 'solucionesgmd.ti@gmail.com'         # Ejemplo: notificaciones@optifire.cl
EMAIL_HOST_PASSWORD = 'yedg eenz duxr slng'  # Contraseña de aplicación (usar variable de entorno en producción)

# Remitente por defecto
DEFAULT_FROM_EMAIL = 'Optifire <notificaciones@optifire.cl>'

# Correo del equipo de Cobranzas / Finanzas
EMAIL_COBRANZA_DESTINO = 'guerraflorescarlos@gmail.com'  # Dirección de cobranza (ajustar en producción)
IVA_CHILE = 0.19 # 19%