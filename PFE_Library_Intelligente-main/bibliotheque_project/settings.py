import os
from pathlib import Path

# 1. المسارات الأساسية
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. إعدادات الأمان
SECRET_KEY = 'django-insecure-@m7ivq&zn#+x10(v_j@x@wy!ke9a8beiiz7qn-=$zmt^wmb5jw'
DEBUG = True
ALLOWED_HOSTS = []

# 3. التطبيقات المسجلة
INSTALLED_APPS = [
    'jazzmin',              # هادي هي اللولة ضروري أ وصال
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gestion_biblio',       # التطبيق ديالك
]

# 4. البرمجيات الوسيطة
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bibliotheque_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bibliotheque_project.wsgi.application'

# 5. قاعدة البيانات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 6. إعدادات الصور والملفات
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 7. إعدادات الدخول والخروج
LOGOUT_REDIRECT_URL = 'home'
LOGIN_REDIRECT_URL = 'mon_espace'

# 8. إعدادات إرسال الإيميلات الاحترافية (Brevo / Sendinblue)
# إعدادات Brevo الاحترافية - النسخة المصححة
# إعدادات Gmail المضمونة 100% للـ PFE
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# إيميلك لي خديتي منو الكود
EMAIL_HOST_USER = 'kachaniwissal@gmail.com' 

# كود الـ 16 حرف لي عاد خديتي دابا (حطيه هنا بلا فراغات)
EMAIL_HOST_PASSWORD ='qghowixpbebnjkbe'

# هاد السطر هو لي كيبان للمستخدم فـ Boîte mail ديالو
DEFAULT_FROM_EMAIL = 'Smart-Biblio <kachaniwissal@gmail.com>'

# 9. إعدادات اللغة والتوقيت
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Casablanca'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JAZZMIN_SETTINGS = {
    "site_title": "Smart Biblio Admin",
    "site_header": "Smart-Biblio",
    "site_brand": "FSBM Library",
    "welcome_sign": "Bienvenue dans l'espace de gestion Smart-Biblio",
    "copyright": "Wissal & Ilham PFE",
    "search_model": ["auth.User", "gestion_biblio.Livre"],
    "show_ui_builder": True, # هادي واعرة: غاتخليك تبدلي الألوان نيشان من السيت!
}