"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.views import APIView
from rest_framework.response import Response


class APIRootView(APIView):
    """
    LifeLink API Root - Lists all available endpoints.
    """
    
    def get(self, request):
        return Response({
            "message": "Welcome to LifeLink API",
            "version": "1.0.0",
            "endpoints": {
                "accounts": "/api/v1/accounts/",
                "sos": "/api/v1/sos/",
                "intelligence": "/api/v1/intelligence/",
                "response": "/api/v1/response/",
                "postcare": "/api/v1/postcare/",
                "admin": "/admin/",
            },
            "documentation": "https://github.com/your-repo/lifelink-api"
        })


urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # API Root
    path('api/v1/', APIRootView.as_view(), name='api-root'),
    
    # LifeLink App Routes
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/sos/', include('sos.urls')),
    path('api/v1/intelligence/', include('intelligence.urls')),
    path('api/v1/response/', include('response.urls')),
    path('api/v1/postcare/', include('postcare.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
]
