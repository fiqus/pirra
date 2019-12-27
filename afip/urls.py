from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^cuit_details/(?P<cuit>\d+)$', views.get_cuit_details, name='help.faqs'),
    re_path(r'^get_ptos_venta/(?P<cuit>\d+)$', views.get_ptos_venta, name='afip.get_ptos_venta'),
]
