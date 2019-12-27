import csv
import logging
from decimal import Decimal
from tempfile import NamedTemporaryFile

from django import http, forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy

from afip.models import AlicuotaIva
from comprobante.models import Comprobante

logger = logging.getLogger(__name__)


def exportar_coleccion_comprobantes(comprobantes, request, file_prefix):
    def importe_formateado(es_cbte_e, cotiz, importe):
        importe = Decimal(importe)
        importe = importe if not es_cbte_e else importe * cotiz
        return "{0:,.4f}".format(importe).replace(',', '').replace('.', ',')

    try:
        with NamedTemporaryFile(mode="w+", prefix=file_prefix, suffix=".csv") as f:
            writer = csv.writer(f)
            writer.writerow(('Fecha Emision', 'Cliente', 'Condicion Iva', 'Localidad', 'CUIT / Nro Doc',
                             'Tipo Comprobante', 'Letra', 'Pto Venta', 'Numero',
                             'Importe no Gravado', 'Importe Neto Gravado', 'EXENTO', 'IVA 0', 'IVA 2,5', 'IVA 5',
                             'IVA 10,5', 'IVA 21', 'IVA 27', 'Tributos', 'Total'))

            for comprobante in comprobantes:
                cbte_json = comprobante.get_json_data()
                es_comprobante_e = comprobante.es_comprobante_e()
                cotizacion = cbte_json['moneda_ctz']
                writer.writerow((cbte_json['fecha_emision'],
                                 cbte_json['cliente']['nombre'],
                                 cbte_json['cliente']['condicion_iva'],
                                 cbte_json['cliente']['localidad'],
                                 cbte_json['cliente']['nro_doc_formatted'],
                                 cbte_json['tipo_cbte']['nombre'],
                                 cbte_json['tipo_cbte']['letra'],
                                 str(cbte_json['punto_vta']),
                                 str(cbte_json['nro']),
                                 importe_formateado(es_comprobante_e, cotizacion, cbte_json['importe_no_gravado']),
                                 importe_formateado(es_comprobante_e, cotizacion, cbte_json['importe_neto_gravado']),
                                 importe_formateado(es_comprobante_e, cotizacion, cbte_json['importe_exento']),
                                 importe_formateado(es_comprobante_e, cotizacion,
                                                    comprobante.importes_ivas[AlicuotaIva.IVA_0_PK][
                                                        'valor']) if AlicuotaIva.IVA_0_PK in comprobante.importes_ivas else "0",
                                 importe_formateado(es_comprobante_e, cotizacion,
                                                    comprobante.importes_ivas[AlicuotaIva.IVA_2_5_PK][
                                                        'valor']) if AlicuotaIva.IVA_2_5_PK in comprobante.importes_ivas else "0",
                                 importe_formateado(es_comprobante_e, cotizacion,
                                                    comprobante.importes_ivas[AlicuotaIva.IVA_5_PK][
                                                        'valor']) if AlicuotaIva.IVA_5_PK in comprobante.importes_ivas else "0",
                                 importe_formateado(es_comprobante_e, cotizacion,
                                                    comprobante.importes_ivas[AlicuotaIva.IVA_10_5_PK][
                                                        'valor']) if AlicuotaIva.IVA_10_5_PK in comprobante.importes_ivas else "0",
                                 importe_formateado(es_comprobante_e, cotizacion,
                                                    comprobante.importes_ivas[AlicuotaIva.IVA_21_PK][
                                                        'valor']) if AlicuotaIva.IVA_21_PK in comprobante.importes_ivas else "0",
                                 importe_formateado(es_comprobante_e, cotizacion,
                                                    comprobante.importes_ivas[AlicuotaIva.IVA_27_PK][
                                                        'valor']) if AlicuotaIva.IVA_27_PK in comprobante.importes_ivas else "0",
                                 importe_formateado(es_comprobante_e, cotizacion, cbte_json['importe_tributos']),
                                 importe_formateado(es_comprobante_e, cotizacion, cbte_json['importe_total'])))
            f.seek(0)
            response = http.HttpResponse(f.read(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + file_prefix + '.csv'
            f.close()
            return response
    except Exception as e:
        logger.exception("Error al exportar comprobantes")
        messages.error(request, str(e))
        return HttpResponseRedirect(reverse_lazy('comprobante.list'))


class ComprobanteExportarMasivoForm(Form):
    exportar_desde = forms.DateField(required=True)
    exportar_hasta = forms.DateField(required=True)


@login_required
def comprobante_exportar_masivo(request):
    form_masivo = ComprobanteExportarMasivoForm()
    if request.method == 'POST':
        form_masivo = ComprobanteExportarMasivoForm(request.POST)
        if form_masivo.is_valid():
            date_from = form_masivo.cleaned_data["exportar_desde"]
            date_to = form_masivo.cleaned_data["exportar_hasta"]
            comprobantes = Comprobante.objects \
                .exclude(cae="") \
                .filter(fecha_emision__range=[date_from, date_to]) \
                .prefetch_related('detallecomprobante_set') \
                .prefetch_related('detallecomprobante_set__alicuota_iva') \
                .prefetch_related('tributocomprobante_set') \
                .prefetch_related('tipo_cbte') \
                .prefetch_related('punto_vta') \
                .prefetch_related('moneda') \
                .prefetch_related('condicion_venta') \
                .prefetch_related('empresa') \
                .prefetch_related('empresa__condicion_iva') \
                .prefetch_related('empresa__condicion_iibb') \
                .prefetch_related('cliente') \
                .prefetch_related('cliente__condicion_iva') \
                .prefetch_related('cliente__tipo_doc').order_by("fecha_emision", "id")

            file_prefix = "comprobantes_desde_" + str(date_from) + "_hasta_" + str(date_to)

            if not comprobantes:
                messages.error(request, "No existen comprobantes para exportar dentro del período seleccionado.")
                return HttpResponseRedirect(reverse_lazy('comprobante.list'))

            return exportar_coleccion_comprobantes(comprobantes, request, file_prefix)
    else:
        return render(request, 'comprobante/comprobante_pre_exportar_masivo.html', {"form": form_masivo})
