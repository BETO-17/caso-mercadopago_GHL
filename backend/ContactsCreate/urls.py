from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_contact, name='create_contact'),
    path('webhook/', views.webhook_contact_created, name='webhook_contact_created'),
]