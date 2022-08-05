import logging
import unicodedata

from django.conf import settings

from comprobante.models import Comprobante
from comprobante.vendor.pyafipws.ws import ws_helper

logger = logging.getLogger(__name__)


def get_normalized_ascii(text):
    return str(unicodedata.normalize('NFKD', text).encode('ascii', 'ignore'))


def autorizar(comprobante, request):
    user = request.user
    return ws_helper.autorizar(comprobante, settings.CERTIFICATE, settings.PRIVATE_KEY, user)


def tiene_detalles_creados(form_data):
    for data in form_data:
        if not data['DELETE']:
            return True
    return False


def get_comprobante_error(comprobante):
    return """Error al autorizar el comprobante con fecha {} del cliente {} por un importe de ${} <br/>
    Se detiene la autorización del resto de los comprobantes. 
    Por favor corrija los errores en el comprobante mencionado y vuelva a intentarlo.<br/>
    """.format(comprobante.fecha_emision, comprobante.cliente.nombre, round(comprobante.importe_neto, 2))


def importe_cbte_asoc_valido(pk, cbte_asoc, detalles, excluir_persistidos):
    if cbte_asoc:
        # comprobantes con mismo comprobante asociado que el que se intenta crear
        comprobantes = Comprobante.objects.filter(cbte_asoc=cbte_asoc)

        if excluir_persistidos:
            # excluyo al mismo comprobante si es una edición, pero no lo excluyo si es una clonación
            comprobantes = comprobantes.exclude(pk=pk)

        importe_total_cbtes = sum(
            comprobante.importe_total * multiplicador(comprobante) for comprobante in comprobantes)

        importe_total_a_validar = sum(detalle.precio_total for detalle in detalles)

        return importe_total_cbtes + importe_total_a_validar <= cbte_asoc.importe_total
    return True


def multiplicador(comprobante):
    return 1 if comprobante.es_factura() or comprobante.es_nota_debito() or comprobante.es_recibo() else -1
