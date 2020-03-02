import datetime
import json
import logging

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

from afip.utils import handler_errores_afip, handler_error_conectividad_afip
from comprobante.models import Comprobante
from comprobante.vendor import pyi25
from comprobante.vendor.pyafipws.ws.soap import SoapFault
from comprobante.vendor.pyafipws.ws.wsfe import WSFEError
from comprobante.views.utils import autorizar, get_comprobante_error
from main.redis import get_redlock_client

logger = logging.getLogger(__name__)


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
    comprobante.cae = ret.CAE
    comprobante.fecha_vto_cae = datetime.datetime.strptime(ret.Vencimiento, "%Y%m%d").date()
    comprobante.motivo = ret.Motivo if not ret.Motivo else ""
    comprobante.resultado = ret.Resultado

    genera_codigo_barra(comprobante)

    # Limpiar errores u observaciones hechas por la AFIP previo a que el cliente las arregle y vuelva a intentar
    if hasattr(ret, 'Errores') and len(ret.Errores):
        comprobante.errores_wsfe = "<br/>".join([e.encode('utf8') for e in ret.Errores])
    else:
        comprobante.errores_wsfe = None

    if hasattr(ret, 'Observaciones') and len(ret.Observaciones):
        comprobante.observaciones_wsfe = "<br />".join([e.encode('utf8') for e in ret.Observaciones])
    else:
        comprobante.observaciones_wsfe = None

    comprobante.set_json_data()
    comprobante.save()


@login_required
@permission_required('comprobante.change_comprobante', raise_exception=True)
def comprobante_autorizar(request, pk):
    comprobante = Comprobante.objects.get(pk=pk)

    if comprobante.cae:
        messages.error(request, "El comprobante ya fue autorizado")
        return HttpResponseRedirect(reverse_lazy('comprobante.list'))

    if request.method == 'POST':

        redlock = get_redlock_client()
        cbte_lock_success = redlock.lock("pirra-cbte_lock-{}-{}".format(comprobante.empresa.nro_doc, comprobante.id),
                                         60)

        if cbte_lock_success:

            try:
                ret = autorizar(comprobante, request)

                display_messages = handler_errores_afip(ret, comprobante)

                if len(display_messages["display_obs"]):
                    messages.warning(request, display_messages["display_obs"])

                if ret.Resultado == "R":
                    messages.error(request,
                                   "Error al autorizar comprobante. <br/>{}".format(display_messages["display_errors"]))
                elif ret.Reproceso == "S":  # WSFEXv1
                    comprobante_guardar_autorizacion(comprobante, ret)
                    messages.success(request, "El comprobante ya había sido autorizado anteriormente. "
                                              "Se le ha asignado el CAE correctamente.")
                elif ret.Resultado == "A":
                    messages.success(request, "Comprobante autorizado correctamente")
                    comprobante_guardar_autorizacion(comprobante, ret)
                elif ret.Resultado == "":
                    if len(display_messages["display_errors"]):
                        messages.error(request,
                                       "Error al autorizar comprobante. {}".format(display_messages["display_errors"]))
                    if len(ret.CAE):
                        comprobante_guardar_autorizacion(comprobante, ret)

                else:
                    messages.error(request, "Error al autorizar comprobante.")

            except SoapFault as e:
                logger.exception("Error al autorizar comprobante")
                messages.error(request, "Error al autorizar comprobante. "
                                        "<br/> Codigo: {}. <br/>"
                                        "{}".format(e.faultcode, handler_error_conectividad_afip(e.faultstring)))
            except WSFEError as e:
                logger.exception("Error al autorizar comprobante")
                messages.error(request, "Error al autorizar comprobante. "
                                        "<br/> Codigo: {}. <br/>"
                                        "{}".format(e.code, handler_error_conectividad_afip(e.msg)))

            except Exception as e:
                logger.exception("Error con conectividad AFIP")
                messages.error(request, handler_error_conectividad_afip(str(e)))

            redlock.unlock(cbte_lock_success)
        else:
            messages.error(request,
                           "Este comprobante ya esta siendo autorizado por otro usuario o proceso. "
                           "Por favor chequée su estado a la brevedad.")

        return HttpResponseRedirect(reverse_lazy('comprobante.list'))
    else:
        # punto_venta_eliminado = PuntoDeVenta.objects.get(pk=comprobante.punto_vta_id).activo
        return render(request, 'comprobante/comprobante_pre_autorizar.html', {"comprobante": comprobante,
                                                                              "punto_venta_eliminado": True})


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
            comprobantes = Comprobante.objects.filter(fecha_emision__range=[date_from, date_to], cae='').order_by(
                'pk')
            comp_pto_vta_eliminado = comprobantes.count()
            comprobantes = comprobantes.filter(punto_vta__activo=True)
            comp_pto_vta_eliminado -= comprobantes.count()

            display_message = ""
            cant = 0
            error = False

            for comprobante in comprobantes:
                try:
                    ret = autorizar(comprobante, request)

                    # si existen errores se guardan en el comprobante pero no se muestran en pantalla
                    handler_errores_afip(ret, comprobante)

                    if ret.Resultado == "R":
                        display_message += get_comprobante_error(comprobante)
                        error = True
                        break
                    elif ret.Reproceso == "S":  # WSFEXv1
                        comprobante_guardar_autorizacion(comprobante, ret)
                        cant += 1
                    elif ret.Resultado == "A":
                        comprobante_guardar_autorizacion(comprobante, ret)
                        cant += 1
                    elif ret.Resultado == "":
                        if len(ret.CAE):
                            comprobante_guardar_autorizacion(comprobante, ret)
                            cant += 1
                        else:
                            display_message += get_comprobante_error(comprobante)
                            error = True
                            break
                    else:
                        display_message += get_comprobante_error(comprobante)
                        error = True
                        break
                except SoapFault as e:
                    display_message += get_comprobante_error(comprobante)
                    display_message += "Codigo del error del Servicio AFIP: {}. <br/>{}".format(e.faultcode,
                                                                                                handler_error_conectividad_afip(
                                                                                                    e.faultstring))
                    error = True
                    break
                except WSFEError as e:
                    display_message += get_comprobante_error(comprobante)
                    display_message += "Codigo del error del Servicio AFIP: {}. <br/>{}".format(e.faultcode,
                                                                                                handler_error_conectividad_afip(
                                                                                                    e.faultstring))
                    error = True
                    break
                except Exception as e:
                    display_message += get_comprobante_error(comprobante)
                    display_message += "Error: {}".format(handler_error_conectividad_afip(e.message))
                    error = True
                    break

            if comp_pto_vta_eliminado:
                display_message += "Se han <strong>ignorado {} comprobantes</strong> porque estaban asociados a un punto de venta eliminado.<br/>".format(
                    comp_pto_vta_eliminado)

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

        comprobantes = Comprobante.objects.filter(pk__in=comp_ids, cae='', punto_vta__activo=True).order_by('pk')
        comp_pto_vta_eliminado = comp_ids.__len__() - comprobantes.count()

        display_message = ""
        cant = 0
        error = False

        for comprobante in comprobantes:
            try:
                ret = autorizar(comprobante, request)

                # si existen errores se guardan en el comprobante pero no se muestran en pantalla
                handler_errores_afip(ret, comprobante)

                if ret.Resultado == "R":
                    display_message += get_comprobante_error(comprobante)
                    error = True
                    break
                elif ret.Reproceso == "S":  # WSFEXv1
                    comprobante_guardar_autorizacion(comprobante, ret)
                    cant += 1
                elif ret.Resultado == "A":
                    comprobante_guardar_autorizacion(comprobante, ret)
                    cant += 1
                elif ret.Resultado == "":
                    if len(ret.CAE):
                        comprobante_guardar_autorizacion(comprobante, ret)
                        cant += 1
                    else:
                        display_message += get_comprobante_error(comprobante)
                        error = True
                        break
                else:
                    display_message += get_comprobante_error(comprobante)
                    error = True
                    break
            except SoapFault as e:
                display_message += get_comprobante_error(comprobante)
                display_message += "Codigo del error del Servicio AFIP: {}. <br/>{}".format(e.faultcode,
                                                                                            handler_error_conectividad_afip(
                                                                                                e.faultstring))
                error = True
                break
            except WSFEError as e:
                display_message += get_comprobante_error(comprobante)
                display_message += "Codigo del error del Servicio AFIP: {}. <br/>{}".format(e.faultcode,
                                                                                            handler_error_conectividad_afip(
                                                                                                e.faultstring))
                error = True
                break
            except Exception as e:
                display_message += get_comprobante_error(comprobante)
                display_message += "Error: {}".format(handler_error_conectividad_afip(e.message))
                error = True
                break

        if comp_pto_vta_eliminado:
            display_message += "Se han <strong>ignorado {} comprobantes</strong> porque estaban asociados a un punto de venta eliminado.<br/>".format(
                comp_pto_vta_eliminado)

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
