from django import forms
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django_tables2 import Table, Column, CheckBoxColumn, TemplateColumn, SingleTableView

from afip.models import TipoComprobante
from comprobante.models import Comprobante
from empresa.models import Cliente, Empresa

COMPROBANTES_PAGE_SIZE = 25


class ComprobanteSearchForm(forms.Form):
    tipo_cbte = forms.ModelChoiceField(queryset=TipoComprobante.objects.none(), required=False,
                                       empty_label="Tipo de Comprobante")
    # cliente = forms.ModelChoiceField(queryset=Cliente.objects.filter(activo=True),
    # required=False, empty_label="Cliente")
    cliente = forms.ModelChoiceField(queryset=Cliente.objects, required=False, empty_label="Cliente")
    fecha_desde = forms.DateField(required=False)
    fecha_hasta = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        super(ComprobanteSearchForm, self).__init__(*args, **kwargs)
        self.fields['tipo_cbte'].queryset = Empresa.objects.first().tipos_cbte


class ComprobanteTable(Table):
    importe_total = Column(orderable=False)

    class Meta:
        attrs = {"id": "comprobantes-table", "class": "table table-responsive-md table-sm table-striped border"}
        model = Comprobante
        per_page = 30
        fields = ("selection", "enviado", "pp_numero", "tipo_cbte", "fecha_emision", "cliente")
        template_name = 'comprobante/table.html'

    @staticmethod
    def render_importe_total(record):
        moneda_simbolo = '$'
        if hasattr(record.moneda, 'simbolo'):
            moneda_simbolo = record.moneda.simbolo
        return moneda_simbolo + "{0:,.2f}".format(record.importe_total)

    @staticmethod
    def render_cliente(record):
        return (record.cliente.nombre[:27] + '..') if len(record.cliente.nombre) > 27 else record.cliente.nombre

    @staticmethod
    def render_has_cae_and_nro(record):
        return record.cae and record.nro

    selection = CheckBoxColumn(accessor='pk', attrs={"th__input": {"id": "selectAll"}}, orderable=False)
    pp_numero = Column(order_by=("punto_vta.id_afip", "nro"), verbose_name="Número")
    tipo_cbte = Column("Tipo Cbte")
    fecha_emision = Column("Fecha")
    cliente = Column("Cliente")
    importe_total = Column("Importe")
    actions = TemplateColumn(template_name='comprobante/comprobante_actions_column.html', orderable=False,
                             verbose_name="Acciones")
    has_cae_and_nro = Column(visible=False, orderable=False, empty_values=())
    enviado = Column(verbose_name="Envío")


class ComprobanteList(SingleTableView):
    model = Comprobante
    table_class = ComprobanteTable
    paginate_by = COMPROBANTES_PAGE_SIZE

    def __init__(self, *args, **kwargs):
        super(ComprobanteList, self).__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.form = ComprobanteSearchForm(self.request.GET or None)
        if not self.request.GET or self.form.is_valid():
            return super(ComprobanteList, self).get(request, *args, **kwargs)
        else:
            return HttpResponseBadRequest()

    def get_queryset(self):
        queryset = Comprobante.objects
        if hasattr(self.form, "cleaned_data"):
            if self.form.cleaned_data["tipo_cbte"]:
                queryset = queryset.filter(tipo_cbte=self.form.cleaned_data["tipo_cbte"])
            if self.form.cleaned_data["cliente"]:
                queryset = queryset.filter(cliente=self.form.cleaned_data["cliente"])
            if self.form.cleaned_data["fecha_desde"]:
                queryset = queryset.filter(fecha_emision__gte=self.form.cleaned_data["fecha_desde"])
            if self.form.cleaned_data["fecha_hasta"]:
                queryset = queryset.filter(fecha_emision__lte=self.form.cleaned_data["fecha_hasta"])
            if self.form.cleaned_data["nro_orden_compra"]:
                queryset = queryset.filter(orden_compra__nro=self.form.cleaned_data["nro_orden_compra"])
        queryset = queryset.order_by("-fecha_emision", "-id")
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ComprobanteList, self).get_context_data(**kwargs)
        context['form'] = self.form

        return context


comprobante_list = login_required(ComprobanteList.as_view())
