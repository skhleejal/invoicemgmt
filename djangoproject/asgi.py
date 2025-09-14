"""
ASGI config for djangoproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import certifi

from django.core.asgi import get_asgi_application

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoproject.settings')

application = get_asgi_application()
