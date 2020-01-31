import datetime
import json
import logging
from copy import deepcopy

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.forms import Form
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt

from comprobante.models import Comprobante
from comprobante.views.utils import importe_cbte_asoc_valido

logger = logging.getLogger(__name__)


def duplicate_comp(comprobante):
    comprobante_copy = deepcopy(comprobante)
    comprobante_copy.pk = None
    comprobante_copy.id = None
    comprobante_copy.id_lote_afip = None
    comprobante_copy.cae = ""
    comprobante_copy.nro = None
    comprobante_copy.codigo_barras_nro = ""
    comprobante_copy.codigo_barras = None
    comprobante_copy.fecha_vto_cae = None
    comprobante_copy.resultado = ""
    comprobante_copy.motivo = None
    comprobante_copy.reproceso = ""
    comprobante_copy.errores_wsfe = None
    comprobante_copy.observaciones_wsfe = None
    comprobante_copy.fecha_emision = datetime.date.today()
    comprobante_copy.fecha_venc_pago = datetime.date.today() + datetime.timedelta(days=30)
    comprobante_copy.enviado = False
    comprobante_copy.cbte_asoc = None
    comprobante_copy.fecha_pago = None
    comprobante_copy.save()
    for detail in comprobante.detallecomprobante_set.all():
        detail_copy = deepcopy(detail)
        detail_copy.id = None
        detail_copy.pk = None

        detail_copy.save()
        comprobante_copy.detallecomprobante_set.add(detail_copy)
    for tributo in comprobante.tributocomprobante_set.all():
        tributo_copy = deepcopy(tributo)
        tributo_copy.id = None
        tributo_copy.pk = None

        tributo_copy.save()
        comprobante_copy.tributocomprobante_set.add(tributo_copy)

    if comprobante.empresa.tiene_opcionales():
        for opcional in comprobante.opcionalcomprobante_set.all():
            opcional_copy = deepcopy(opcional)
            opcional_copy.id = None
            opcional_copy.pk = None

            opcional_copy.save()
            comprobante_copy.opcionalcomprobante_set.add(opcional_copy)
    comprobante_copy.save()


@login_required()
@csrf_exempt
@permission_required('comprobante.add_comprobante', raise_exception=True)
def comprobante_duplicate(request, pk):
    comprobante = Comprobante.objects.get(pk=pk)
    if not importe_cbte_asoc_valido(pk, comprobante.cbte_asoc, comprobante.detallecomprobante_set.all(), False):
        error = "El importe del comprobante a crear hace que se supere el importe ${0:.2f} del comprobante asociado al mismo.".format(
            comprobante.cbte_asoc.importe_total)
        messages.error(request, error)
        return HttpResponseRedirect(reverse_lazy('comprobante.list'))

    duplicate_comp(comprobante)

    messages.success(request, " Comprobante duplicado correctamente.")

    return HttpResponseRedirect(reverse_lazy('comprobante.list'))


class ComprobanteDuplicarMasivoSeleccionForm(Form):
    nros_comp_duplicar = forms.IntegerField(required=False)

@csrf_exempt
@login_required
@permission_required('comprobante.add_comprobante', raise_exception=True)
def comprobante_duplicar_masivo_seleccion(request):
    form_masivo = ComprobanteDuplicarMasivoSeleccionForm()
    comp_ids = []
    if request.method == 'POST':
        display_message = ""
        cant = 0
        comp_ids = json.loads(request.POST["nros_comp_duplicar"])

        comprobantes = Comprobante.objects.filter(pk__in=comp_ids, punto_vta__activo=True).order_by('pk')
        comp_pto_vta_eliminado = comp_ids.__len__() - comprobantes.count()

        for comprobante in comprobantes:
            duplicate_comp(comprobante)
            cant += 1

        if comp_pto_vta_eliminado:
            display_message += "Se han <strong>ignorado {} comprobantes</strong> porque estaban asociados a un punto de venta eliminado.<br/>".format(
                comp_pto_vta_eliminado)

        if cant > 0:
            display_message += "Duplicación masiva realizada con éxito. <br/> Se han duplicado {} comprobantes.".format(
                cant)
            result_type = 'success'
        else:
            display_message += "No se encontraron comprobantes para el rango de fechas ingresadas. <br/>"
            result_type = 'warning'

        result = {
            'cant': str(cant),
            'result': display_message,
            'result_type': result_type
        }
        return HttpResponse(
            json.dumps(result),
            content_type="application/json"
        )
    else:
        comprobantes_list = json.loads(request.GET["comprobantes"])
        comp_list = []
        for comp in comprobantes_list:
            comp_list.append(comp)

        pks_list = json.loads(request.GET["pks"])
        for pk in pks_list:
            comp_ids.append(int(pk.get("value")))

        return render_to_response('comprobante/comprobante_pre_duplicar_masivo_seleccion.html',
                                  {"form": form_masivo,
                                   "nros_comp_duplicar": comp_ids,
                                   "comprobantes_list": comprobantes_list},
                                  RequestContext(request))
