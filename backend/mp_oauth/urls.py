from django.urls import path
from . import views

urlpatterns = [
    path('install/mp/', views.install_link_mp, name='mp_install'),
    path('oauth/callback/mp/', views.mp_callback, name='mp_callback'),  # Con slash
]
