from django.urls import path

from . import views

urlpatterns = [
    path('preguntas_frecuentes', views.faqs, name='help.faqs'),
    path('dev_help', views.dev_help, name='help.dev_help'),
]
