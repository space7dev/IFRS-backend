import environ

from .base import *

env = environ.Env()
environ.Env.read_env()
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    'default': {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": env("POSTGRES_DB", default=os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": env("POSTGRES_USER", default="user"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="password"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

# change
ALLOWED_HOSTS = env.list("SERVERNAMES", default="localhost")

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

ANYMAIL = {
    "SENDGRID_API_KEY": env("SENDGRID_API_KEY", default=""),
}

EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="xxxx@gmail.com")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="xxxx@gmail.com")
EMAIL_PORT = 587
EMAIL_USE_TLS = bool(env("EMAIL_USE_TLS", default=True))
SERVER_EMAIL = env("SERVER_EMAIL", default="xxxx@gmail.com")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="mypassword")


# Use this var to identify commit info at the top of the app - Don't use this in Production Environment
REPO_DIR = env("REPO_DIR", default='')

CUSTOMER_SERVICE = env("CUSTOMER_SERVICE", default="")

# CORS & CSRF SETTINGS
CORS_ORIGIN_WHITELIST = env.list("CORS_ORIGIN_WHITELIST", default=[
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:3000"
])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    "http://localhost:8000",
    "http://localhost:80",
    "http://127.0.0.1:80",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
])
CORS_ALLOW_HEADERS = env.list("CORS_ALLOW_HEADERS", default=[
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "session-user-id",
])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "http://localhost:8080",
    "http://localhost:3000"
])

OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
