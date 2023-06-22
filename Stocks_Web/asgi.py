"""
ASGI config for {{ project_name }} project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/{{ docs_version }}/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import account.routing


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Stocks_Web.settings")

application = ProtocolTypeRouter(
    {   "https": get_asgi_application(),
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                    account.routing.websocket_urlpatterns
                )
            )
    }
)