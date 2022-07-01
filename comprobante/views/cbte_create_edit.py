import datetime
import logging

import simplejson
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.forms import ModelForm, HiddenInput, modelformset_factory, Select
from django.forms.utils import flatatt
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.encoding import force_text
from django.utils.html import format_html

from afip.models import TipoComprobante, AlicuotaIva, Unidad, Tributo, Moneda
from comprobante.models import Comprobante, DetalleComprobante, TributoComprobante, OpcionalComprobante
from comprobante.views.utils import tiene_detalles_creados, importe_cbte_asoc_valido
from empresa.models import Empresa, PuntoDeVenta, Cliente, Producto
from main.widgets import SelectAlicuotaIva
from user.models import ProxiUser

logger = logging.getLogger(__name__)


class ConditionalValidateForm(ModelForm):
    def validate_required_field(self, cleaned_data, field_name, message="Este campo es requerido"):
        if field_name in cleaned_data and cleaned_data[field_name] is None:
            self._errors[field_name] = self.error_class([message])
            del cleaned_data[field_name]


class ComprobanteForm(ConditionalValidateForm):
    class Meta:
        model = Comprobante
        fields = (
            "id", 'empresa', 'punto_vta', 'concepto', 'tipo_cbte', 'condicion_venta', 'condicion_venta_texto',
            'remito_nro', 'cbte_asoc', 'fecha_pago',
            'fecha_emision', 'fecha_venc_pago', 'cliente',
            'tipo_expo', 'moneda', 'idioma', 'incoterms', 'pais_destino', 'id_impositivo', 'moneda_ctz',
            'forma_pago',
            'observaciones', 'observaciones_comerciales', 'incoterms_ds', 'descuento', 'importe_total')
        widgets = {
            'empresa': HiddenInput
        }

    def clean_fecha_venc_pago(self):
        fecha_emision = self.cleaned_data.get("fecha_emision")
        fecha_venc_pago = self.cleaned_data.get("fecha_venc_pago")
        if fecha_venc_pago < fecha_emision:
            self.add_error("fecha_venc_pago",
                           "La fecha de vencimiento de pago debe ser mayor a la fecha de emisión del comprobante.")
            raise forms.ValidationError(
                "La fecha de vencimiento de pago debe ser mayor a la fecha de emisión del comprobante.")

        return fecha_venc_pago

    def clean(self):
        cleaned_data = super(ComprobanteForm, self).clean()
        if cleaned_data.get("tipo_cbte").id_afip == 19:
            self.validate_required_field(cleaned_data, 'tipo_expo')
            self.validate_required_field(cleaned_data, 'moneda')
            self.validate_required_field(cleaned_data, 'moneda_ctz')
            self.validate_required_field(cleaned_data, 'idioma')
            self.validate_required_field(cleaned_data, 'pais_destino')
            if cleaned_data.get("pais_destino") is None:
                self.validate_required_field(cleaned_data, 'id_impositivo')

        if cleaned_data.get("tipo_cbte").id_afip in (TipoComprobante.NC_E, TipoComprobante.ND_E):
            self.validate_required_field(cleaned_data, 'cbte_asoc')

        if cleaned_data.get("tipo_cbte").id_afip == TipoComprobante.FACTURA_E:
            self.validate_required_field(cleaned_data, 'fecha_pago')

        dto = cleaned_data.get("descuento")
        if dto:
            if dto < 0 or dto > 100:
                self.add_error("descuento",
                               "El descuento a aplicar por porcentaje debe ser mayor a 0 (cero) y menor a 100 (cien).")
                raise forms.ValidationError(
                    "El descuento a aplicar por porcentaje debe ser mayor a 0 (cero) y menor a 100 (cien).")

            if "descuento" in self.errors:
                del self.errors["descuento"]

        return cleaned_data

    def clean_cbte_asoc(self):
        cbte_asoc = self.cleaned_data['cbte_asoc']
        tipo_cbte = self.cleaned_data.get("tipo_cbte").id_afip
        if tipo_cbte in (TipoComprobante.NC_E, TipoComprobante.ND_E):
            if not cbte_asoc:
                error = "Debe informar un comprobante asociado"
                self.add_error("cbte_asoc", error)
            else:
                try:
                    cbte = Comprobante.objects.get(pk=cbte_asoc.id)
                    if cbte.tipo_cbte.id_afip != TipoComprobante.FACTURA_E:
                        error = "El comprobante elegido no es una factura de exportacion"
                        self.add_error("cbte_asoc", error)
                    if not cbte.cae:
                        error = "El comprobante elegido no esta autorizado"
                        self.add_error("cbte_asoc", error)
                except Comprobante.DoesNotExist:
                    error_log = "Error al consultar comprobante asociado:{}-{}-{}".format(cbte_asoc.tipo_cbte.nombre,
                                                                                          cbte_asoc.tipo_cbte.letra,
                                                                                          cbte_asoc.nro)
                    logger.error(error_log)
                    error = "Hubo un error al querer validar el comprobante asociado"
                    self.add_error("cbte_asoc", error)
        return cbte_asoc

    def clean_fecha_pago(self):
        fecha_pago = self.cleaned_data['fecha_pago']
        tipo_cbte = self.cleaned_data.get("tipo_cbte").id_afip

        if tipo_cbte == TipoComprobante.FACTURA_E:
            if not fecha_pago:
                error = "Debe informar una fecha de pago"
                self.add_error("fecha_pago", error)
            else:
                if fecha_pago < datetime.date.today():
                    error = "La fecha de pago debe ser mayor o igual a hoy"
                    self.add_error("fecha_pago", error)
        return fecha_pago

    tipo_cbte = forms.ModelChoiceField(queryset=TipoComprobante.objects.none())
    importe_total = forms.DecimalField(max_digits=19, decimal_places=4)
    descuento = forms.DecimalField(widget=forms.NumberInput(attrs={'placeholder': 'Inserte un porcentaje',
                                                                   'class': 'form-control',
                                                                   'min': '0',
                                                                   'max': '100'}), required=False)
    # Muestro solo facturas E autorizadas, es decir con cae != ''
    cbte_asoc = forms.ModelChoiceField(
        queryset=Comprobante.objects.filter(tipo_cbte=TipoComprobante.FACTURA_E_PK).exclude(cae=''), required=False,
        label="Factura asociada", empty_label="Ingrese numero")

    def __init__(self, *args, **kwargs):
        empresa = Empresa.objects.first()
        super(ComprobanteForm, self).__init__(*args, **kwargs)
        self.fields['cliente'].empty_label = ""
        self.fields['concepto'].initial = empresa.concepto
        self.fields['punto_vta'].queryset = PuntoDeVenta.objects.filter(activo=True)
        # self.fields['punto_vta'].queryset = PuntoDeVenta.objects.all()
        # self.fields['cliente'].queryset = Cliente.objects.all()
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)
        self.fields['tipo_cbte'].initial = empresa.tipos_cbte.first()
        self.fields['tipo_cbte'].queryset = empresa.tipos_cbte.all()
        self.fields['cbte_asoc'].queryset = Comprobante.objects.filter(tipo_cbte=TipoComprobante.FACTURA_E_PK)


class DecimalWithStepAny(forms.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, {"type": self.input_type, "name": name})
        if value != '':
            final_attrs['value'] = force_text(self.format_value(value))
            final_attrs['title'] = final_attrs['title'].encode('ascii',
                                                               'ignore')  # para que no haya errores con format_html()
        return format_html('<input step="any" type="number" {0} />', flatatt(final_attrs))


class ComprobanteDetalleForm(ModelForm):
    class Meta:
        model = DetalleComprobante
        fields = ("id", "cant", "unidad", "producto", "detalle", "precio_unit", "alicuota_iva")
        widgets = {
            'cant': DecimalWithStepAny(),
            'precio_unit': DecimalWithStepAny(),
        }

    alicuota_iva = forms.ModelChoiceField(queryset=AlicuotaIva.objects.order_by("id_afip"), required=False,
                                          widget=SelectAlicuotaIva, empty_label=None)
    # producto = forms.ModelChoiceField(queryset=Producto.objects.filter(activo=True), required=False, empty_label="")
    producto = forms.ModelChoiceField(queryset=Producto.objects, required=False, empty_label="")
    unidad = forms.ModelChoiceField(queryset=Unidad.objects.exclude(id_afip=Unidad.BONIFICACION_ID_AFIP), required=True)

    def clean_alicuota_iva(self):
        if self.cleaned_data["alicuota_iva"] is None:
            return AlicuotaIva.objects.get(id_afip=AlicuotaIva.NO_GRAVADO)
        return self.cleaned_data["alicuota_iva"]

    def __init__(self, *args, **kwargs):
        super(ComprobanteDetalleForm, self).__init__(*args, **kwargs)
        # self.fields['producto'].queryset = Producto.objects.filter(activo=True)
        self.fields['producto'].queryset = Producto.objects.all()

    # Si se le pasa initial data al formset y dichos datos no son modificados en pantalla
    # los mismos no son validados ni guardados. Es por eso que se sobreescribe este metodo, para que
    # en caso de que el formset tenga inital tome como que cada form fue modificado y lo valide y persista

    def has_changed(self):
        changed_data = super(ModelForm, self).has_changed()
        return self.initial or changed_data


DetalleComprobanteFormSet = modelformset_factory(DetalleComprobante, ComprobanteDetalleForm, can_delete=True, extra=0)


class ComprobanteTributoForm(ModelForm):
    class Meta:
        model = TributoComprobante
        fields = ("id", "tributo", "detalle", "base_imponible", "alicuota")

    tributo = forms.ModelChoiceField(queryset=Tributo.objects.all(), required=True, widget=Select, empty_label=None)

    # Si se le pasa initial data al formset y dichos datos no son modificados en pantalla
    # los mismos no son validados ni guardados. Es por eso que se sobreescribe este metodo, para que
    # en caso de que el formset tenga inital tome como que cada form fue modificado y lo valide y persista
    def has_changed(self):
        changed_data = super(ModelForm, self).has_changed()
        return self.initial or changed_data


TributoComprobanteFormSet = modelformset_factory(TributoComprobante, ComprobanteTributoForm, can_delete=True, extra=0)


class OpcionalComprobanteForm(ModelForm):
    class Meta:
        model = OpcionalComprobante
        fields = ("id", "opcional", "valor")


OpcionalComprobanteFormSet = modelformset_factory(OpcionalComprobante, OpcionalComprobanteForm, can_delete=False,
                                                  extra=0)


def generar_descuentos_por_alicuota(comprobante):
    # regenero los descuentos por alicuota
    comprobante.detallecomprobante_set.filter(unidad__id_afip=Unidad.BONIFICACION_ID_AFIP).delete()

    if comprobante.descuento:
        # creo un descuento por cada alicuota de iva
        unidad_bonificacion = Unidad.objects.filter(id_afip=99).first()
        for detalle in comprobante.detallecomprobante_set. \
                exclude(unidad=unidad_bonificacion.id).order_by('alicuota_iva'):
            # TODO: Armar la estructura en memoria para después persistir de una vez. Así es muy poco performante.
            dto_existente = comprobante.detallecomprobante_set.filter(alicuota_iva=detalle.alicuota_iva,
                                                                      unidad__id_afip=Unidad.BONIFICACION_ID_AFIP).first()
            importe_neto_descuento = detalle.importe_neto * comprobante.descuento / 100
            importe_iva_descuento = detalle.importe_iva * comprobante.descuento / 100
            if dto_existente:
                detalle_id = dto_existente.id
                precio_unit_con_iva = (dto_existente.precio_unitario_con_iva
                                       - importe_iva_descuento - importe_neto_descuento)
                importe_neto_descuento = dto_existente.importe_neto - importe_neto_descuento
            else:
                detalle_id = None
                importe_neto_descuento *= -1
                precio_unit_con_iva = importe_neto_descuento + importe_iva_descuento * -1

            detalle_descuento_global = DetalleComprobante(
                alicuota_iva=detalle.alicuota_iva,
                cant=1,
                precio_unit=importe_neto_descuento,
                producto=None,
                detalle="Descuento global",
                unidad=unidad_bonificacion,
                id=detalle_id,
                pk=detalle_id,
                comprobante_id=comprobante.id)

            if dto_existente:
                detalle_descuento_global.save(force_update=True)
            else:
                detalle_descuento_global.save()


@login_required()
@permission_required('comprobante.add_comprobante', raise_exception=True)
def comprobante_create_edit(request, pk=None):
    productos = simplejson.dumps({p.id: {
        "nombre": str(p),
        "precio_unit": p.precio_unit,
        "alicuota_iva": p.alicuota_iva_id,
        "unidad": p.unidad_id} for p in Producto.objects.filter(activo=True)})
        # "unidad": p.unidad_id} for p in Producto.objects.all()})

    empresa = Empresa.objects.first()
    opcionales = empresa.get_opcionales()
    rgs = empresa.get_resoluciones_generales()

    if empresa.tiene_opcionales():
        cant_opcionales = opcionales.count()
    else:
        cant_opcionales = 0

    if pk:
        # Edicion de  cbte
        comprobante = Comprobante.objects.get(pk=pk)
        if comprobante.cae or comprobante.nro:
            if comprobante.cae:
                messages.error(request, "El comprobante ya fue autorizado y no puede ser modificado")
            else:
                messages.error(request,
                               "El comprobante fue enviado a la AFIP y todavía no obtuvimos una respuesta. "
                               "No puede ser modificado")
            return HttpResponseRedirect(reverse_lazy('comprobante.list'))
        else:
            detalles = comprobante.detallecomprobante_set.exclude(unidad__id_afip=Unidad.BONIFICACION_ID_AFIP)
            comp_tributos = comprobante.tributocomprobante_set.all()
            comp_opcionales = comprobante.opcionalcomprobante_set.all()
            OpcionalComprobanteFormSet.extra = cant_opcionales - comp_opcionales.count() \
                if comp_opcionales.count() < cant_opcionales else 0
            formset_opcional = OpcionalComprobanteFormSet(request.POST or None, queryset=comp_opcionales,
                                                          prefix='opcionales')
    else:
        # Creacion de un nuevo comprobante
        detalles = DetalleComprobante.objects.none()
        comprobante = None
        comp_tributos = TributoComprobante.objects.none()

        comp_opcionales = OpcionalComprobante.objects.none()
        initial = []
        for opcional in opcionales:
            initial.append({"opcional": opcional.pk})
        initial = list(reversed(initial))
        OpcionalComprobanteFormSet.extra = cant_opcionales
        formset_opcional = OpcionalComprobanteFormSet(request.POST or None,
                                                      queryset=comp_opcionales,
                                                      initial=initial,
                                                      prefix='opcionales')

    tiene_cbtes = empresa.tieneTiposCbte
    # tiene_puntos_de_venta = PuntoDeVenta.objects.filter(activo=True).count() > 0
    tiene_puntos_de_venta = PuntoDeVenta.objects.count() > 0
    form = ComprobanteForm(request.POST or None, instance=comprobante)

    formset_detalle = DetalleComprobanteFormSet(request.POST or None, queryset=detalles, prefix='detalles')

    formset_tributo = TributoComprobanteFormSet(request.POST or None, queryset=comp_tributos, prefix='tributos')

    unidades = Unidad.objects.all()
    alicuotas_iva = AlicuotaIva.objects.all().order_by('id_afip')
    tributos = Tributo.objects.all()

    if request.method == 'POST':

        if form.is_valid() \
                and formset_detalle.is_valid() \
                and formset_tributo.is_valid() \
                and formset_opcional.is_valid() > 0:  # All validation rules pass

            if not hasattr(formset_tributo, "cleaned_data"):
                messages.error(request, "Hay un error en el formulario, por favor intente nuevamente.")
            elif not hasattr(formset_detalle, "cleaned_data") or not tiene_detalles_creados(formset_detalle.cleaned_data):
                messages.error(request, "Debe cargar algún item en el detalle del comprobante.")
            else:
                comprobante = form.save(commit=False)

                detalles = formset_detalle.save(commit=False)
                comp_tributos = formset_tributo.save(commit=False)
                comp_opcionales = formset_opcional.save(commit=False)

                if not importe_cbte_asoc_valido(pk, comprobante.cbte_asoc, detalles, True):
                    error = "El importe del comprobante a crear hace que se supere el importe " \
                            "${0:.2f} del comprobante asociado al mismo.".format(comprobante.cbte_asoc.importe_total)
                    messages.error(request, error)
                else:
                    comprobante.save()

                    comprobante.detallecomprobante_set.add(*detalles, bulk=False)
                    comprobante.tributocomprobante_set.add(*comp_tributos, bulk=False)
                    comprobante.opcionalcomprobante_set.add(*comp_opcionales, bulk=False)

                    if not comprobante.es_comprobante_e():
                        moneda_local = Moneda.objects.get(id_afip=settings.MONEDA_LOCAL)
                        if moneda_local:
                            comprobante.moneda_id = moneda_local.pk
                        comprobante.moneda_ctz = settings.MONEDA_LOCAL_CTZ

                    for detalle in formset_detalle.deleted_objects:
                        detalle.delete()
                    for tributo in formset_tributo.deleted_objects:
                        tributo.delete()

                    comprobante.save()
                    generar_descuentos_por_alicuota(comprobante)
                    comprobante.save()

                    return HttpResponseRedirect(reverse_lazy('comprobante.list'))

    if not tiene_cbtes or not tiene_puntos_de_venta:
        return render(request, "comprobante/comprobante_error.html")

    return render(request, "comprobante/comprobante_form.html",
                  {"form": form, "formset_detalle": formset_detalle, "formset_tributo": formset_tributo,
                   "formset_opcional": formset_opcional, "unidades": unidades,
                   "alicuotas_iva": alicuotas_iva, "tributos": tributos, "empresa": empresa,
                   "exento_id": AlicuotaIva.EXENTO_PK, "no_gravado_id": AlicuotaIva.NO_GRAVADO_PK,
                   "factura_e_id": TipoComprobante.FACTURA_E_PK, "nc_e_id": TipoComprobante.NC_E_PK,
                   "nd_e_id": TipoComprobante.ND_E_PK, "factura_a_id": TipoComprobante.FACTURA_A_PK,
                   "nc_a_id": TipoComprobante.NC_A_PK, "nd_a_id": TipoComprobante.ND_A_PK,
                   "factura_m_id": TipoComprobante.FACTURA_M_PK,
                   "nc_m_id": TipoComprobante.NC_M_PK, "nd_m_id": TipoComprobante.ND_M_PK,
                   "productos": productos, "tiene_opcionales": empresa.tiene_opcionales(),
                   "factura_b_id": TipoComprobante.FACTURA_B_PK, "nc_b_id": TipoComprobante.NC_B_PK,
                   "nd_b_id": TipoComprobante.ND_B_PK, "recibo_b_id": TipoComprobante.RECIBO_B_PK,
                   "factura_c_id": TipoComprobante.FACTURA_C_PK, "nc_c_id": TipoComprobante.NC_C_PK,
                   "nd_c_id": TipoComprobante.ND_C_PK, "recibo_c_id": TipoComprobante.RECIBO_C_PK,
                   "object": comprobante,
                   "rgs": rgs,
                   "opcionales": opcionales})
