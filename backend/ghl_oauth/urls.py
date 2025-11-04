from django.urls import path
from . import views

urlpatterns = [
    path('install/ghl/', views.install_link, name='ghl_install'),
    path('oauth/callback/ghl', views.ghl_callback, name='ghl_callback'),
    path('oauth/callback/', views.ghl_callback, name='ghl_callback_alias'),
]
