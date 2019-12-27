from django.contrib import admin
from comprobante.models import Comprobante, DetalleComprobante

admin.register(Comprobante)
admin.register(DetalleComprobante)