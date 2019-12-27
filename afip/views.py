import json
from comprobante.vendor.pyafipws.ws.ws_helper import setupWSFE, get_cert_and_key, setupWSFEX
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from afip.models import Padron
from empresa.models import PuntoDeVenta
import logging

logger = logging.getLogger(__name__)


def get_cuit_details(request, cuit):
    item = get_object_or_404(Padron, cuit=cuit)

    return JsonResponse({
        "cuit": item.cuit,
        "denominacion": item.denominacion,
        "imp_ganancias": item.imp_ganancias,
        "condicion_iva": item.get_condicion_iva()
    })


def get_ptos_venta(request, cuit):
    cert, key = get_cert_and_key(settings.CERTIFICATE, settings.PRIVATE_KEY)
    wsfe = setupWSFE(int(cuit), cert, key)
    wsfex = setupWSFEX(int(cuit), cert, key)

    ptos_venta = wsfe.ParamGetPtosVenta()
    ptos_venta_importados = guardar_ptos_vta_importados(ptos_venta, 'local')

    ptos_venta_expo = wsfex.GetParamPtosVenta()
    ptos_venta_importados += guardar_ptos_vta_importados(ptos_venta_expo, 'exportacion')

    return ptos_venta_importados


def guardar_ptos_vta_importados(ptos_venta, mercado):
    importados = 0
    if ptos_venta:
        for pto in ptos_venta:
            bloqueado, fecha_baja, id_afip = parse_pto_vta_afip(mercado, pto)
            bloqueado = bloqueado.split(':')[1] != 'N'
            dado_de_baja = fecha_baja.split(':')[1] != 'NULL' and fecha_baja.split(':')[1] != 'None'
            id_afip = int(id_afip)
#            existe_en_bd = PuntoDeVenta.objects.filter(id_afip=id_afip, activo=True).exists()
            existe_en_bd = PuntoDeVenta.objects.filter(id_afip=id_afip).exists()
            if not bloqueado and not dado_de_baja and not existe_en_bd:
                pto_vta = PuntoDeVenta()
                pto_vta.id_afip = id_afip
                pto_vta.nombre = id_afip
                pto_vta.save()
                importados += 1
    return importados


def parse_pto_vta_afip(mercado, pto):
    if mercado == 'local':
        id_afip, emision_tipo, bloqueado, fecha_baja = pto.split('|')
    else:
        id_afip, bloqueado, fecha_baja = pto.split('|')
    return bloqueado, fecha_baja, id_afip
