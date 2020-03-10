import io as StringIO
import json
import logging
import zipfile
from tempfile import NamedTemporaryFile

from django import forms
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt

from comprobante.models import Comprobante
from comprobante.views.cbte_pdf import gen_pdf_file

logger = logging.getLogger(__name__)


def imprimir_coleccion_comprobantes(comprobantes, request, zip_prefix):
    try:
        ultimo_procesado = None
        with NamedTemporaryFile(prefix=zip_prefix, suffix=".zip") as f:
            with zipfile.ZipFile(f, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
                for comprobante in comprobantes:
                    ultimo_procesado = str(comprobante.pp_numero) + comprobante.cliente.nombre
                    pdf = StringIO.BytesIO()
                    try:
                        gen_pdf_file(pdf, comprobante, True)
                        filename = "{}_{}_{}_{}_{}.pdf".format(comprobante.tipo_cbte.nombre,
                                                               comprobante.tipo_cbte.letra,
                                                               comprobante.pp_numero,
                                                               comprobante.cliente.tipo_doc.nombre,
                                                               comprobante.cliente.nro_doc)
                        zf.writestr(filename, pdf.read())
                    finally:
                        pdf.close()
            f.seek(0)
            response = http.HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=' + zip_prefix + '.zip'
            return response
    except Exception as e:
        messages.error(request, str(e))
        logger.exception("Error al procesar CBTE: " + ultimo_procesado)
        return HttpResponseRedirect(reverse_lazy('comprobante.list'))


class ComprobanteImprimirMasivoForm(Form):
    imprimir_desde = forms.DateField(required=True)
    imprimir_hasta = forms.DateField(required=True)


@login_required
def comprobante_imprimir_masivo(request):
    form_masivo = ComprobanteImprimirMasivoForm()
    if request.method == 'POST':
        form_masivo = ComprobanteImprimirMasivoForm(request.POST)
        if form_masivo.is_valid():
            date_from = form_masivo.cleaned_data["imprimir_desde"]
            date_to = form_masivo.cleaned_data["imprimir_hasta"]
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
                .prefetch_related('cliente__tipo_doc')

            zip_prefix = "comprobantes_desde_" + str(date_from) + "_hasta_" + str(date_to)

            if not comprobantes:
                messages.error(request, "No existen comprobantes para imprimir dentro del período seleccionado.")
                return HttpResponseRedirect(reverse_lazy('comprobante.list'))

            return imprimir_coleccion_comprobantes(comprobantes, request, zip_prefix)
    else:
        return render_to_response('comprobante/comprobante_pre_imprimir_masivo.html', {"form": form_masivo},
                                  RequestContext(request))


class ComprobanteImprimirMasivoSeleccionForm(Form):
    nros_comp_imprimir = forms.IntegerField(required=False)


@csrf_exempt
@login_required
def comprobante_imprimir_masivo_seleccion(request):
    form_masivo = ComprobanteImprimirMasivoSeleccionForm()
    comp_ids = []
    if request.method == 'POST':
        form_masivo = ComprobanteImprimirMasivoSeleccionForm(request.POST)
        valores = eval(form_masivo['nros_comp_imprimir'].value())

            # .exclude(cae="") \
        selected_objects = Comprobante.objects \
            .filter(pk__in=valores) \
            .prefetch_related('detallecomprobante_set') \
            .prefetch_related('detallecomprobante_set__alicuota_iva') \
            .prefetch_related('tributocomprobante_set') \
            .select_related('tipo_cbte') \
            .select_related('punto_vta') \
            .select_related('moneda') \
            .select_related('condicion_venta') \
            .select_related('empresa') \
            .prefetch_related('empresa__condicion_iva') \
            .prefetch_related('empresa__condicion_iibb') \
            .select_related('cliente') \
            .prefetch_related('cliente__condicion_iva') \
            .prefetch_related('cliente__tipo_doc')

        if not selected_objects:
            messages.error(request,
                           "No se han encontrado comprobantes autorizados para imprimir dentro de los que ha seleccionado.")
            return HttpResponseRedirect(reverse_lazy('comprobante.list'))

        zip_prefix = "comprobantes_desde_" + str(selected_objects[0].nro) + "_hasta_" + str(
            selected_objects[selected_objects.count() - 1].nro)

        return imprimir_coleccion_comprobantes(selected_objects, request, zip_prefix)
    else:
        comprobantes_list = json.loads(request.GET["comprobantes"])
        comp_list = []
        for comp in comprobantes_list:
            comp_list.append(comp)

        pks_list = json.loads(request.GET["pks"])
        for pk in pks_list:
            comp_ids.append(int(pk.get("value")))

        return render_to_response('comprobante/comprobante_pre_imprimir_masivo_seleccion.html',
                                  {"form": form_masivo,
                                   "nros_comp_imprimir": comp_ids,
                                   "comprobantes_list": comprobantes_list},
                                  RequestContext(request))
