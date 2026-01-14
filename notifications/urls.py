from django.urls import path
from .views import RegisterTokenView

urlpatterns = [
    path('register-token/', RegisterTokenView.as_view(), name='register-token'),
]
