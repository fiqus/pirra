import datetime
import io
import json
import logging
import zipfile
from io import StringIO
from tempfile import NamedTemporaryFile

from dateutil.relativedelta import relativedelta
from django import forms
from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import EmailMultiAlternatives
from django.forms import Form
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render_to_response
from django.template import Context
from django.template import RequestContext
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView

from afip.models import TipoComprobanteAlicuotaIva, AlicuotaIva
from comprobante.models import Comprobante, MailEnviadoComprobante, \
    OrdenCompra
from comprobante.vendor.pyafipws.ws import ws_helper
from comprobante.views.cbte_list import COMPROBANTES_PAGE_SIZE
from comprobante.views.cbte_pdf import gen_pdf_file
from comprobante.views.utils import get_normalized_ascii
from empresa.models import Empresa, Cliente
from empresa.views import ClienteForm
from main.redis import get_redis_client

logger = logging.getLogger(__name__)


class ComprobanteEliminarMasivoForm(Form):
    eliminar_desde = forms.DateField(required=True)
    eliminar_hasta = forms.DateField(required=True)


@csrf_exempt
@login_required
@permission_required('comprobante.delete_comprobante', raise_exception=True)
def comprobante_eliminar_masivo(request):
    form_masivo = ComprobanteEliminarMasivoForm()
    if request.method == 'POST':
        form_masivo = ComprobanteEliminarMasivoForm(request.POST)
        if form_masivo.is_valid():
            date_from = form_masivo.cleaned_data["eliminar_desde"]
            date_to = form_masivo.cleaned_data["eliminar_hasta"]
            comprobantes = Comprobante.objects.filter(fecha_emision__range=[date_from, date_to], cae='')
            display_message = ""
            error = False
            cant = comprobantes.count()

            try:
                comprobantes.delete()
                # debo calcularlo asi porque en django 1.8 delete no devuelve deleted_objects
                cant = cant - comprobantes.count()
            except Exception as e:
                display_message += "Error: {}".format(e.message)
                error = True

            if error:
                result_type = 'danger'
            else:
                if cant > 0:
                    display_message += "Eliminación masiva realizada con éxito. <br/>"
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
                'result': 'No posee un plan con los permisos necesarios para realizar esta accion.',
                'result_type': 'danger'
            }
            return HttpResponse(
                json.dumps(result),
                content_type="application/json"
            )
    else:
        return render_to_response('comprobante/comprobante_pre_eliminar_masivo.html', {"form": form_masivo},
                                  RequestContext(request))


class ComprobanteEliminarMasivoSeleccionForm(Form):
    nros_comp_eliminar = forms.IntegerField(required=False)


@csrf_exempt
@login_required
@permission_required('comprobante.delete_comprobante', raise_exception=True)
def comprobante_eliminar_masivo_seleccion(request):
    form_masivo = ComprobanteEliminarMasivoSeleccionForm()
    comp_ids = []
    if request.method == 'POST':
        comp_ids = json.loads(request.POST["nros_comp_eliminar"])

        comprobantes = Comprobante.objects.filter(pk__in=comp_ids, cae='')
        display_message = ""
        cant = comprobantes.count()
        error = False

        orders_id = [oc.id for oc in OrdenCompra.objects.filter(comprobante__id__in=comp_ids, comprobante__cae='')]

        try:
            comprobantes.delete()
            # debo calcularlo asi porque en django 1.8 delete no devuelve deleted_objects
            cant = cant - comprobantes.count()
        except Exception as e:
            display_message += "Error: {}".format(e.message)
            error = True

        if error:
            result_type = 'danger'
        else:
            if cant > 0:
                display_message += "Eliminación masiva realizada con éxito. <br/>"
                result_type = 'success'
            else:
                display_message += "No se encontraron comprobantes a eliminar entre los seleccionados. <br/>"
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

        return render_to_response('comprobante/comprobante_pre_eliminar_masivo_seleccion.html',
                                  {"form": form_masivo,
                                   "nros_comp_eliminar": comp_ids,
                                   "comprobantes_list": comprobantes_list},
                                  RequestContext(request))


class ComprobanteEnviarMasivoSeleccionForm(Form):
    nros_comp_enviar = forms.IntegerField(required=False)


@csrf_exempt
@login_required
def comprobante_enviar_masivo_seleccion(request):
    form_masivo = ComprobanteEnviarMasivoSeleccionForm()
    comp_ids = []
    if request.method == 'POST':
        comp_ids = json.loads(request.POST["nros_comp_enviar"])
        empresa = Empresa.objects.first()

        comprobantes = Comprobante.objects.filter(pk__in=comp_ids).exclude(cae='')
        comprobantes = comprobantes[:COMPROBANTES_PAGE_SIZE]
        display_message = ""
        cant = 0
        cant_error = 0
        error = False
        sent_comprobantes_list = []

        for comp in comprobantes:
            sent_comp = comp.tipo_cbte.nombre + " " + comp.tipo_cbte.letra + " " + comp.pp_numero
            if comp.cliente.email:
                try:
                    text_content = generate_and_send_comp_mail(comp, empresa, comp.cliente.email, "")

                    cant += 1
                    status = "Ok"
                    error_sending = False
                except Exception as e:
                    status = "Error"
                    display_message += "Error: {}".format(e.message)
                    error = True
                    error_sending = True
                finally:
                    comp.enviado = True
                    comp.save()

                    mail_enviado_comprobante = MailEnviadoComprobante(comprobante=comp,
                                                                      email=comp.cliente.email,
                                                                      fecha_envio=datetime.datetime.now(),
                                                                      estado=status, texto=text_content)
                    mail_enviado_comprobante.save()
                    status = "Enviado"
            else:
                status = "Email de cliente incompleto"
                cant_error += 1
                error_sending = True

            sent_comprobantes_list.append({"comp": sent_comp, "status": status, "error": error_sending})

        if error:
            result_type = 'danger'
        else:
            if cant > 0:
                display_message += "Envío masivo realizado con éxito. <br/>"
                result_type = 'success'
                if cant_error > 0:
                    display_message += "Por favor revise los errores antes de reenviar los comprobantes."
            else:
                display_message += "No se encontraron comprobantes a enviar entre los seleccionados. <br/>"
                result_type = 'warning'

        result = {
            'cant': str(cant),
            'result': display_message,
            'result_type': result_type,
            "sent_comprobantes_list": sent_comprobantes_list
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

        return render_to_response('comprobante/comprobante_pre_enviar_masivo_seleccion.html',
                                  {"form": form_masivo,
                                   "nros_comp_enviar": comp_ids,
                                   "comprobantes_list": comprobantes_list},
                                  RequestContext(request))


def generate_and_send_comp_mail(comprobante, empresa, mail_to, message):
    file_to_send = io.BytesIO()
    try:
        gen_pdf_file(file_to_send, comprobante, False)
        plaintext = get_template('comprobante/email/enviar_factura.txt')
        htmly = get_template('comprobante/email/enviar_factura.html')
        d = {'msg': message, 'name': empresa.nombre, 'empresa_email': empresa.email}
        text_content = plaintext.render(d)
        html_content = htmly.render(d)
        cc = ()
        if empresa.mandar_copia_comprobante:
            cc = (empresa.email,)
        mail = EmailMultiAlternatives("[{}] - Comprobante Electrónico".format(empresa.nombre),
                                      text_content, settings.DEFAULT_FROM_EMAIL, [mail_to],
                                      headers={'Reply-To': empresa.email, "X-Mailin-tag": "comprobante"},
                                      cc=cc)
        mail.attach_alternative(html_content, "text/html")
        fname = "comprobante-{}.pdf".format(comprobante.pp_numero) if comprobante.nro else "comprobante.pdf"
        mail.attach(fname, file_to_send.read(), 'application/pdf')
        mail.send()
    finally:
        file_to_send.close()

    return text_content


@login_required
@csrf_exempt
def enviar_comp_mail(request, pk):
    comprobante = Comprobante.objects.get(pk=pk)
    if not comprobante:
        raise RuntimeError("Id de comprobante inválido.")

    return render_to_response('comprobante/comprobante_enviar_mail.html',
                              {"comprobante": comprobante,
                               "envio_desde_listado": True},
                              RequestContext(request))


@login_required
@csrf_exempt
def enviar_factura(request):
    response_dict = {}
    try:
        pk = request.POST["pk"]
        comprobante = Comprobante.objects.get(pk=pk)
        empresa = Empresa.objects.first()
        text_content = generate_and_send_comp_mail(comprobante, empresa, request.POST["email"], request.POST["message"])

        response_dict['status'] = "Ok"
        response_dict['success'] = True
        response_dict['message'] = "La factura se envio correctamente"

    except Exception as e:
        response_dict['status'] = "Error"
        response_dict['success'] = False
        response_dict['message'] = str(e)

    finally:
        comprobante.enviado = True
        comprobante.save()

        mailEnviadoComprobante = MailEnviadoComprobante(comprobante=comprobante, email=request.POST["email"],
                                                        fecha_envio=datetime.datetime.now(),
                                                        estado=response_dict['status'], texto=text_content)
        mailEnviadoComprobante.save()

        return http.HttpResponse(json.dumps(response_dict), content_type="application/json")


@login_required
def exportar_citi_ventas(request):
    return render_to_response('comprobante/exportar_citi_ventas.html',
                              {"year": datetime.datetime.now().year, "last_year": datetime.datetime.now().year - 1},
                              RequestContext(request))


@login_required
def historial_envios(request, pk):
    comprobante = Comprobante.objects.get(pk=pk)
    if not comprobante:
        raise RuntimeError("Id de comprobante inválido.")

    return render_to_response('comprobante/historial_enviados.html',
                              {"comprobante": comprobante.get_data_para_imprimir(),
                               "envios": comprobante.mailenviadocomprobante_set.all()},
                              RequestContext(request))


class ClienteListDialog(ListView):
    model = Cliente
    template_name = 'comprobante/cliente_dialog_list.html'

    def get_queryset(self):
        return Cliente.objects.all()


cliente_list_dialog = login_required(ClienteListDialog.as_view())


class ClienteNewDialog(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'comprobante/cliente_dialog_new.html'

    def form_invalid(self, form):
        return JsonResponse({'error': form.errors})

    def form_valid(self, form):
        new_cliente = form.save()
        return JsonResponse({'pk': new_cliente.pk, 'nombre': new_cliente.nombre, 'nro_doc': new_cliente.nro_doc})

    @method_decorator(permission_required("empresa.add_cliente", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ClienteNewDialog, self).dispatch(*args, **kwargs)


cliente_new_dialog = login_required(ClienteNewDialog.as_view())


@login_required
@csrf_exempt
def get_porcentaje_impuesto(request, pk):
    try:
        tipo_cbte = TipoComprobanteAlicuotaIva.objects.get(pk=pk)
        response_dict = {}
        response_dict['status'] = "Ok"
        response_dict['success'] = True
        response_dict['id'] = str(tipo_cbte.pk)
        response_dict['name'] = str(tipo_cbte.alicuota_iva)
        response_dict['porcentaje'] = str(tipo_cbte.alicuota_iva.porc)
        return http.HttpResponse(json.dumps(response_dict), content_type="application/json")
    except Exception as e:
        response_dict = {}
        response_dict['status'] = "error"
        response_dict['success'] = False
        response_dict['message'] = e.message
        return http.HttpResponse(json.dumps(response_dict), content_type="application/json")


@login_required
def generar_citi_ventas(request):
    exportar_mes = request.GET.get('exportar_mes', datetime.date.today().month)
    exportar_anio = request.GET.get('exportar_anio', datetime.date.today().year)
    comprobantes = Comprobante.objects.exclude(cae="").filter(fecha_emision__month=exportar_mes,
                                                              fecha_emision__year=exportar_anio)
    data_cbtes = ""
    data_alicuotas = ""
    try:
        for comprobante in comprobantes:
            if comprobante.es_citi_ventas():
                alicuotas_grouped = comprobante.alicuotas_grouped
                cant_alicuotas = "1" if comprobante.es_comprobante_e() or len(alicuotas_grouped) == 0 else str(
                    len(alicuotas_grouped))
                # Facturas de exportacion informan importe total en pesos: importe * cotizacion
                importe_total = comprobante.importe_total if not comprobante.es_comprobante_e() else comprobante.importe_total * comprobante.moneda_ctz
                importe_neto_no_gravado = comprobante.importe_no_gravado if not comprobante.es_comprobante_e() else 0
                data_cbtes += comprobante.fecha_emision.strftime('%Y%m%d').zfill(8)
                data_cbtes += str(comprobante.tipo_cbte.id_afip).zfill(3)
                data_cbtes += str(comprobante.punto_vta.id_afip).zfill(5)
                data_cbtes += str(comprobante.nro).zfill(20)
                data_cbtes += str(comprobante.nro).zfill(20)  # nro cbte hasta
                data_cbtes += str(comprobante.cliente.tipo_doc.id_afip).zfill(2)
                data_cbtes += comprobante.cliente.nro_doc[:20].zfill(20)
                data_cbtes += get_normalized_ascii(comprobante.cliente.nombre)[:30].ljust(30)
                data_cbtes += str("{:016.2f}".format(importe_total)).replace(".", "")
                data_cbtes += str("{:016.2f}".format(importe_neto_no_gravado)).replace(".", "")
                data_cbtes += str(0).zfill(15)  # percep a no categ
                data_cbtes += str("{:016.2f}".format(comprobante.importe_exento)).replace(".", "")
                data_cbtes += str("{:016.2f}".format(comprobante.importe_tributos_nacionales)).replace(".", "")
                data_cbtes += str("{:016.2f}".format(comprobante.importe_tributos_provinciales)).replace(".", "")
                data_cbtes += str("{:016.2f}".format(comprobante.importe_tributos_municipales)).replace(".", "")
                data_cbtes += str("{:016.2f}".format(comprobante.importe_tributos_internos)).replace(".", "")
                data_cbtes += str(comprobante.moneda.id_afip) if comprobante.moneda else "PES"
                data_cbtes += ("{:011.6f}".format(comprobante.moneda_ctz)).replace(".",
                                                                                   "") if comprobante.moneda_ctz else "0001000000"
                data_cbtes += cant_alicuotas
                data_cbtes += comprobante.codigo_operacion
                data_cbtes += str("{:016.2f}".format(comprobante.importe_tributos_otro)).replace(".", "")
                data_cbtes += "00000000" if comprobante.es_comprobante_e() else comprobante.fecha_venc_pago.strftime(
                    '%Y%m%d').zfill(8)
                data_cbtes += "\r\n"
                if (int(cant_alicuotas) != len(alicuotas_grouped) and int(cant_alicuotas) != 1 and len(
                        alicuotas_grouped) != 0):
                    raise RuntimeError(
                        "Error al generar REGINFO. Comprobante conflictivo: {} {}".format(comprobante.tipo_cbte,
                                                                                          comprobante.pp_numero))
                if len(alicuotas_grouped) == 0:
                    # no gravado o exento
                    data_alicuotas += str(comprobante.tipo_cbte.id_afip).zfill(3)
                    data_alicuotas += str(comprobante.punto_vta.id_afip).zfill(5)
                    data_alicuotas += str(comprobante.nro).zfill(20)
                    data_alicuotas += "000000000000000"
                    data_alicuotas += str(AlicuotaIva.IVA_0).zfill(4)
                    data_alicuotas += "000000000000000"
                    data_alicuotas += "\r\n"
                else:
                    for id_afip, alicuota in list(alicuotas_grouped.items()):
                        # En reg inf vtas la factura e informa neto gravado como el total del comprobante e iva cero
                        importe_neto_gravado = alicuota[
                            'importe_neto_gravado'] if not comprobante.es_comprobante_e() else importe_total
                        data_alicuotas += str(comprobante.tipo_cbte.id_afip).zfill(3)
                        data_alicuotas += str(comprobante.punto_vta.id_afip).zfill(5)
                        data_alicuotas += str(comprobante.nro).zfill(20)
                        data_alicuotas += str("{:016.2f}".format(importe_neto_gravado)).replace(".", "")
                        data_alicuotas += str(id_afip).zfill(4)
                        data_alicuotas += str(
                            "{:016.2f}".format(alicuota['importe_neto_gravado'] * alicuota['porc'] / 100)).replace(
                            ".",
                            "")
                        data_alicuotas += "\r\n"
        with NamedTemporaryFile(prefix="reginfo_", suffix=".zip") as f:
            with zipfile.ZipFile(f, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("VENTAS_CBTE_{}-{}.txt".format(exportar_anio, exportar_mes.zfill(2)), data_cbtes)
                zf.writestr("VENTAS_ALICUOTAS_{}-{}.txt".format(exportar_anio, exportar_mes.zfill(2)),
                            data_alicuotas)
            f.seek(0)
            response = http.HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="REGINFO_VENTAS_AFIP_{}-{}.zip"'.format(
                exportar_anio, exportar_mes.zfill(2))
            return response
    except Exception as e:
        messages.error(request, str(e))
        logger.exception("error al generar citi ventas")
        return HttpResponseRedirect(reverse_lazy('comprobante.list'))


def check_status(request):
    r = get_redis_client()
    data = r.get("pirra-afip-status")
    if not data:
        resp = ws_helper.check_status(settings.CUIT_TO_CONNECT, settings.CERTIFICATE, settings.PRIVATE_KEY)
        data = json.dumps(resp)
        r.set("pirra-afip-status", data)
        r.expireat("pirra-afip-status", datetime.datetime.now() + relativedelta(minutes=10))
    if data:
        return JsonResponse(json.loads(data))
    return JsonResponse({"AppServerStatus": "ok", "DbServerStatus": "ok", "AuthServerStatus": "ok"})
