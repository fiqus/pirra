import datetime
import json
import logging
import random

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import Form
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt

from comprobante.models import Comprobante
from comprobante.vendor import pyi25
from comprobante.vendor.pyafipws.ws.soap import SoapFault
from comprobante.vendor.pyafipws.ws.wsfe import WSFEError
from comprobante.views.utils import autorizar, get_comprobante_error
from main.redis import get_redlock_client

logger = logging.getLogger(__name__)

def generar_cae():
    cae = ""

    for x in range(14):
        number = str(random.randrange(0, 9))
        cae += number

    return cae

def sig_nro_cbte():
    return str(Comprobante.objects.exclude(cae="").count() + 1)

class Ret():
    def __init__(self, cbte_nro):
        self.Resultado = "A"
        self.CAE = generar_cae()
        self.CbteNro = cbte_nro
        self.Vencimiento = "20250325"
        self.Resultado = ""
        self.Motivo = ""
        self.Observaciones = ""
        self.Reproceso = ""
        self.Errores = ""

def genera_codigo_barra(comprobante):
    generador = pyi25.PyI25()

    cod_aux = comprobante.empresa.nro_doc
    cod_aux += str(comprobante.tipo_cbte.id_afip)
    cod_aux += str(comprobante.punto_vta.id_afip)
    cod_aux += str(comprobante.cae)
    cod_aux += comprobante.fecha_vto_cae.strftime("%Y%m%d")
    cod_aux += generador.DigitoVerificadorModulo10(cod_aux)
    comprobante.codigo_barras_nro = cod_aux

    filename = str(datetime.datetime.now()) + comprobante.pp_numero + ".jpg"

    tmpfile_io = generador.GenerarImagen(cod_aux, filename, 9, 0, 90, "JPEG")

    image_file = InMemoryUploadedFile(tmpfile_io, None, filename, 'image/jpeg', tmpfile_io.getbuffer().nbytes, None)
    comprobante.codigo_barras.save(filename, image_file)


def comprobante_guardar_autorizacion(comprobante, ret):
    comprobante.nro = ret.CbteNro
    comprobante.cae = ret.CAE
    comprobante.fecha_vto_cae = datetime.datetime.strptime(ret.Vencimiento, "%Y%m%d").date()
    comprobante.motivo = ret.Motivo if not ret.Motivo else ""
    comprobante.resultado = ret.Resultado

    genera_codigo_barra(comprobante)

    # No esta autorizando con AFIP y no va a devolver Erores u Obsevaciones
    if hasattr(ret, 'Errores') and len(ret.Errores):
        comprobante.errores_wsfe = b"<br/>".join([e.encode('utf8') for e in ret.Errores])
    else:
        comprobante.errores_wsfe = None

    if hasattr(ret, 'Observaciones') and len(ret.Observaciones):
        comprobante.observaciones_wsfe = b"<br />".join([e.encode('utf8') for e in ret.Observaciones])
    else:
        comprobante.observaciones_wsfe = None

    comprobante.set_json_data()
    comprobante.save()


@login_required
@permission_required('comprobante.change_comprobante', raise_exception=True)
def comprobante_autorizar(request, pk):
    comprobante = Comprobante.objects.get(pk=pk)

    if request.method == 'POST':
        cbte_nro = sig_nro_cbte()
        ret = Ret(cbte_nro)
        redlock = get_redlock_client()
        cbte_lock_success = redlock.lock("pirra-cbte_lock-{}-{}".format(comprobante.empresa.nro_doc, comprobante.id),
                                         60)

        if cbte_lock_success:

            messages.success(request, "Comprobante autorizado correctamente")
            comprobante_guardar_autorizacion(comprobante, ret)

            redlock.unlock(cbte_lock_success)
        else:
            messages.error(request,
                           "Este comprobante ya esta siendo autorizado por otro usuario o proceso. "
                           "Por favor chequée su estado a la brevedad.")

        return HttpResponseRedirect(reverse_lazy('comprobante.list'))
    else:
        # punto_venta_eliminado = PuntoDeVenta.objects.get(pk=comprobante.punto_vta_id).activo
        return render(request, 'comprobante/comprobante_pre_autorizar.html', {"comprobante": comprobante,
                                                                              "punto_venta_eliminado": True,
                                                                              "existe_cae": comprobante.cae,
                                                                              "cliente_activo": comprobante.cliente.activo})


class ComprobanteAutorizarMasivoForm(Form):
    autorizar_desde = forms.DateField(required=True)
    autorizar_hasta = forms.DateField(required=True)


@csrf_exempt
@login_required
@permission_required('comprobante.change_comprobante', raise_exception=True)
def comprobante_autorizar_masivo(request):
    form_masivo = ComprobanteAutorizarMasivoForm()
    if request.method == 'POST':
        form_masivo = ComprobanteAutorizarMasivoForm(request.POST)
        if form_masivo.is_valid():
            date_from = form_masivo.cleaned_data["autorizar_desde"]
            date_to = form_masivo.cleaned_data["autorizar_hasta"]
            comprobantes = Comprobante.objects.filter(fecha_emision__range=[date_from, date_to], cae='').order_by('pk')

            comp_pto_vta_eliminado = comprobantes.count()
            comprobantes = comprobantes.filter(punto_vta__activo=True)
            comp_pto_vta_eliminado -= comprobantes.count()

            comp_cliente_eliminado = comprobantes.count()
            comprobantes = comprobantes.filter(cliente__activo=True)
            comp_cliente_eliminado -= comprobantes.count()

            display_message = ""
            cant = 0
            error = False

            for comprobante in comprobantes:
                cbte_nro = sig_nro_cbte()
                ret = Ret(cbte_nro)
                comprobante_guardar_autorizacion(comprobante, ret)
                cant += 1

            if comp_pto_vta_eliminado:
                display_message += "Se han <strong>ignorado {} comprobantes</strong> porque estaban asociados a un punto de venta eliminado.<br/>".format(
                    comp_pto_vta_eliminado)

            if comp_cliente_eliminado:
                display_message += "Se han <strong>ignorado {} comprobantes</strong> porque estaban asociados a un cliente eliminado.<br/>".format(
                    comp_cliente_eliminado)

            if error:
                result_type = 'danger'
            else:
                if cant > 0:
                    display_message += "Autorización masiva realizada con éxito. <br/>"
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
            result = {
                'cant': '0',
                'result': 'Hay errores en el formulario. Por favor, corríjalos y vuelva a intentarlo.',
                'result_type': 'danger'
            }
            return HttpResponse(
                json.dumps(result),
                content_type="application/json"
            )
    else:
        return render_to_response('comprobante/comprobante_pre_autorizar_masivo.html', {"form": form_masivo},
                                  RequestContext(request))


class ComprobanteAutorizarMasivoSeleccionForm(Form):
    nros_comp_autorizar = forms.IntegerField(required=False)


@csrf_exempt
@login_required
@permission_required('comprobante.change_comprobante', raise_exception=True)
def comprobante_autorizar_masivo_seleccion(request):
    form_masivo = ComprobanteAutorizarMasivoSeleccionForm()
    comp_ids = []
    if request.method == 'POST':
        comp_ids = json.loads(request.POST["nros_comp_autorizar"])

        comprobantes = Comprobante.objects.filter(pk__in=comp_ids, cae='').order_by('pk')

        comp_pto_vta_eliminado = comprobantes.count()
        comprobantes = comprobantes.filter(punto_vta__activo=True)
        comp_pto_vta_eliminado -= comprobantes.count()

        comp_cliente_eliminado = comprobantes.count()
        comprobantes = comprobantes.filter(cliente__activo=True)
        comp_cliente_eliminado -= comprobantes.count()        

        display_message = ""
        cant = 0
        error = False

        for comprobante in comprobantes:
            cbte_nro = sig_nro_cbte()
            ret = Ret(cbte_nro)
            comprobante_guardar_autorizacion(comprobante, ret)
            cant += 1

        if comp_pto_vta_eliminado:
            display_message += "Se han <strong>ignorado {} comprobantes</strong> porque estaban asociados a un punto de venta eliminado.<br/>".format(
                comp_pto_vta_eliminado)

        if comp_cliente_eliminado:
            display_message += "Se han <strong>ignorado {} comprobantes</strong> porque estaban asociados a un cliente eliminado.<br/>".format(
                comp_cliente_eliminado)

        if error:
            result_type = 'danger'
        else:
            if cant > 0:
                display_message += "Autorización masiva realizada con éxito. <br/> Se han autorizado {} comprobantes.".format(
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

        return render_to_response('comprobante/comprobante_pre_autorizar_masivo_seleccion.html',
                                  {"form": form_masivo,
                                   "nros_comp_autorizar": comp_ids,
                                   "comprobantes_list": comprobantes_list},
                                  RequestContext(request))
