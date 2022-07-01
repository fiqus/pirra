# coding=utf-8
import datetime

from django.urls import reverse_lazy, reverse

from afip.views import get_ptos_venta
from comprobante.csv_import import import_product_csv, import_client_csv
from comprobante.models import Comprobante, DetalleComprobante, DetalleOrdenCompra, OrdenCompra
from decimal import Decimal
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.db.models import F
from django.forms import ModelForm, Form, CharField, TextInput, ModelMultipleChoiceField, CheckboxSelectMultiple, \
    ClearableFileInput, FileField
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_tables2 import SingleTableView, Table, A, TemplateColumn, Column
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.views.generic import UpdateView, CreateView, DeleteView
from afip.models import TipoComprobante, TipoDoc, CondicionIva, ResolucionGeneral, AlicuotaIva, Unidad
from empresa.models import Empresa, PuntoDeVenta, Cliente, Producto
from main.table2_columns import EditColumn, MoneyColumn, DeleteColumn
from main.widgets import TextInputWithButton, SelectAlicuotaIva
from django.utils.safestring import mark_safe
import logging
import codecs

from user.models import ProxiUser

logger = logging.getLogger(__name__)

permisos_explicacion = mark_safe(
    '<strong>Administracion de usuarios</strong>: Permite dar de alta usuarios en el sistema e imprimir comprobantes<br/> ' +
    '<strong>Facturacion clientes</strong>: Permite crear, autorizar e imprimir comprobantes y crear clientes<br/> ' +
    '<strong>Administracion de empresa</strong>: Permite configurar la empresa; gestionar los productos, los clientes y los puntos de venta; imprimir comprobantes')


class ImagePreviewWidget(ClearableFileInput):
    url_markup_template = '<a href="{0}" class="img-upload-preview"><img src="{0}"/></a>'


class EmpresaForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EmpresaForm, self).__init__(*args, **kwargs)
        self.fields['nombre'].label = 'Razón social'
        self.fields['nro_doc'].label = 'CUIT'
        self.fields['cod_postal'].label = 'Código postal'
        self.fields[
            'email'].help_text = 'Coloque el email de la empresa, este email va a servir de contacto para sus clientes.'
        self.fields['condicion_iva'].label = 'Condición IVA'
        self.fields['condicion_iibb'].label = 'Condición IIBB'
        self.fields['nro_iibb'].label = 'Número IIBB'
        self.fields[
            'concepto'].help_text = 'Campo opcional. Si elige un concepto, el mismo será el predeterminado para cada vez que crée un comprobante'
        self.fields['tipos_cbte'].label = 'Tipos de comprobante que realiza'
        self.fields['resoluciones_generales'].label = 'Resoluciones Generales alcanzadas para la facturación'
        self.fields[
            'resoluciones_generales'].help_text = 'Si su empresa se encuentra sujeta a alguna de las resoluciones listadas arriba, debe seleccionarla para poder ver los campos opcionales que se atienen a la misma al momento de emitir sus comprobantes.'
        self.fields['fecha_serv_desde'].label = 'Inicio de actividades'
        self.fields['fecha_serv_desde'].help_text = 'El formato de la fecha debe ser: DD/MM/AAAA'
        self.fields['fecha_serv_hasta'].label = 'Fin de actividades'
        self.fields['fecha_serv_hasta'].help_text = 'El formato de la fecha debe ser: DD/MM/AAAA'
        self.fields['mandar_copia_comprobante'].label = 'Enviarme una copia de los comprobantes que envio por mail.'
        self.fields[
            'mandar_copia_comprobante'].help_text = 'La copia del email será enviada a la casilla que configuró para su empresa, en el campo "Email" de este mismo formulario.'
        self.fields['mandar_copia_comprobante'].widget.attrs['class'] = 'mandarCopiaOrigenInput'
        self.fields['imprimir_comp_triplicado'].label = 'Imprimir comprobante por duplicado y triplicado'
        self.fields['imprimir_comp_triplicado'].widget.attrs['class'] = 'imprimirDuplicadoYTriplicadoInput'

        self.fields['logo'].help_text = 'Formatos válidos: *.png / *.jpg'

        # Si el usuario no tiene un plan EDI oculto la opcion de empresa con EDI
        self.fields['utiliza_edi'].widget = forms.HiddenInput()

    def _clean_readonly_field(self, fname):
        return self.initial[fname]

    def clean_nro_doc(self):
        return self.instance.nro_doc

    class Meta:
        model = Empresa
        fields = ['nro_doc', 'nombre', 'domicilio', 'localidad', 'cod_postal', 'email', 'condicion_iva',
                  'condicion_iibb', 'nro_iibb', 'concepto',
                  'tipos_cbte', 'resoluciones_generales', 'fecha_serv_desde', 'fecha_serv_hasta',
                  'mandar_copia_comprobante',
                  'imprimir_comp_triplicado', 'logo', 'utiliza_edi']

    nro_doc = CharField(widget=TextInput(attrs={'readonly': 'readonly'}))
    tipos_cbte = ModelMultipleChoiceField(queryset=TipoComprobante.objects.all(),
                                          widget=CheckboxSelectMultiple)

    resoluciones_generales = ModelMultipleChoiceField(queryset=ResolucionGeneral.objects.all(), required=False,
                                                      widget=CheckboxSelectMultiple)
    nombre = forms.CharField(max_length=100)
    logo = forms.ImageField(widget=ImagePreviewWidget, required=False)


class MessageUpdateView(UpdateView):
    def form_valid(self, form):
        response = super(MessageUpdateView, self).form_valid(form)
        messages.success(self.request, 'Se han guardado los cambios exitosamente')
        return response

    def form_invalid(self, form):
        response = super(MessageUpdateView, self).form_invalid(form)
        messages.error(self.request, 'Hay errores en el formulario.')
        return response


class EmpresaUpdate(MessageUpdateView):
    model = Empresa
    form_class = EmpresaForm
    success_url = "/empresa/empresa"

    def get_object(self, queryset=None):
        return Empresa.objects.first()

    @method_decorator(permission_required("empresa.change_empresa", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(EmpresaUpdate, self).dispatch(*args, **kwargs)


empresa_update = login_required(EmpresaUpdate.as_view())


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2", "first_name", "last_name", "email", "is_active",
                  "groups"]

    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        self.fields['groups'].label = 'Permisos del usuario'
        self.fields['groups'].help_text = permisos_explicacion

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            user.groups.set(self.cleaned_data["groups"])
            user.save()
        return user


class UserUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active",
                  "groups"]

    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['groups'].label = 'Permisos del usuario'
        self.fields['groups'].help_text = permisos_explicacion

    def _clean_readonly_field(self, fname):
        return self.initial[fname]


class UserTable(Table):
    class Meta:
        attrs = {"id": "users-table"}
        model = User
        per_page = 10
        fields = ("username", "email", "groups", "is_active", "is_superuser")

    groups = TemplateColumn(template_name='auth/groups_column.html', orderable=False)
    actions = EditColumn('user.update', kwargs={"pk": A('pk')}, orderable=False, accessor='pk', verbose_name="Acciones")


class UserList(SingleTableView):
    model = User
    table_class = UserTable


user_list = login_required(UserList.as_view())


class UserCreate(CreateView):
    model = User
    form_class = UserCreateForm
    success_url = reverse_lazy('user.list')

    @method_decorator(permission_required("auth.add_user", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(UserCreate, self).dispatch(*args, **kwargs)


user_create = login_required(UserCreate.as_view())


class UserUpdate(MessageUpdateView):
    model = User
    form_class = UserUpdateForm
    success_url = reverse_lazy('user.list')

    @method_decorator(permission_required("auth.change_user", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(UserUpdate, self).dispatch(*args, **kwargs)


user_update = login_required(UserUpdate.as_view())


class PuntoDeVentaForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PuntoDeVentaForm, self).__init__(*args, **kwargs)
        self.fields['id_afip'].help_text = "Este campo hace referencia al identificador que otorga la AFIP al crear un " \
                                           + "punto de venta. Para más información, dirijase a nuestra sección de " + \
                                           "<a target='_blank' href='" + str(
            reverse('help.faqs')) + "'>Preguntas Frecuentes.</a>"

    class Meta:
        fields = ["id_afip", "nombre"]
        model = PuntoDeVenta


class PuntoDeVentaTable(Table):
    class Meta:
        attrs = {"id": "puntos-venta-table"}
        model = PuntoDeVenta
        per_page = 10
        fields = ("id_afip", "nombre")

    actions = EditColumn('punto_de_venta.update', kwargs={"pk": A('pk')}, orderable=False, accessor='pk',
                         verbose_name="Acciones")
    delete = DeleteColumn('punto_de_venta.delete', kwargs={"pk": A('pk')}, orderable=False, accessor='pk',
                          verbose_name=" ")


class PuntoDeVentaList(SingleTableView):
    model = PuntoDeVenta
    table_class = PuntoDeVentaTable
    queryset = PuntoDeVenta.objects.filter(activo=True)
   # queryset = PuntoDeVenta.objects.all()


punto_de_venta_list = login_required(PuntoDeVentaList.as_view())


class PuntoDeVentaCreate(CreateView):
    model = PuntoDeVenta
    form_class = PuntoDeVentaForm
    success_url = reverse_lazy('punto_de_venta.list')

    @method_decorator(permission_required("empresa.add_puntodeventa", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(PuntoDeVentaCreate, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        proxi_user = ProxiUser.objects.get(user=self.request.user)
        company = proxi_user.company
        form.instance.empresa = company
        return super().form_valid(form)


punto_de_venta_create = login_required(PuntoDeVentaCreate.as_view())


class PuntoDeVentaUpdate(MessageUpdateView):
    model = PuntoDeVenta
    form_class = PuntoDeVentaForm
    success_url = reverse_lazy('punto_de_venta.list')

    @method_decorator(permission_required("empresa.change_puntodeventa", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(PuntoDeVentaUpdate, self).dispatch(*args, **kwargs)


punto_de_venta_update = login_required(PuntoDeVentaUpdate.as_view())


class PuntoDeVentaDelete(DeleteView):
    model = PuntoDeVenta
    success_url = reverse_lazy('punto_de_venta.list')

    @method_decorator(permission_required("empresa.delete_puntodeventa", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(PuntoDeVentaDelete, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PuntoDeVentaDelete, self).get_context_data(**kwargs)
        context['cant_comp_asociados'] = Comprobante.objects.filter(punto_vta=self.object).count()
        context['entidad_a_borrar'] = "punto de venta"
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.activo = False
        self.object.fecha_baja = datetime.date.today()
        self.object.usuario_baja = request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


punto_de_venta_delete = login_required(PuntoDeVentaDelete.as_view())


@csrf_exempt
@login_required
def get_ptos_venta_afip(request):
    if request.method == 'POST':
        try:
            ptos_venta_importados = get_ptos_venta(request, Empresa.objects.first().nro_doc)
            if not ptos_venta_importados:
                messages.error(request, "No hay puntos de venta para importar.")
            else:
                messages.success(request, 'Se importaron con exito {} puntos de venta.'.format(ptos_venta_importados))
        except Exception as e:
            logger.error(str(e))
            messages.error(request,
                           "Se produjo un error al intentar importar sus puntos de venta. Vuelva a intentarlo mas tarde o  comuniquese con el equipo tecnico de Pirra.")
        finally:
            return HttpResponseRedirect(reverse_lazy('punto_de_venta.list'))
    else:
        return render(request, 'empresa/importar_ptos_vta_afip.html')


class ClienteForm(ModelForm):
    tipo_doc = forms.ModelChoiceField(queryset=TipoDoc.objects.all(), label='Tipo de documento')
    nro_doc = forms.CharField(label='Número de documento')
    nombre = forms.CharField(label='Nombre o Razón Social')
    condicion_iva = forms.ModelChoiceField(queryset=CondicionIva.objects.all(), label='Condición IVA')
    telefono = forms.CharField(label='Teléfono', required=False)

    def __init__(self, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Cliente
        exclude = ('editable',)

    nro_doc = CharField(widget=TextInputWithButton(btn_attrs={
        'label': 'Buscar',
        'type': 'button',
        'placement': 'append',
        'class': 'btn btn-default btn-search-cuit'
    }))

    def clean_nro_doc(self):
        return self.cleaned_data["nro_doc"].replace("-", "")


class ClienteSearchForm(Form):
    nombre = forms.CharField(label="Nombre", required=False)
    doc = forms.CharField(label="Documento", required=False)
    activo = forms.BooleanField(label="Solo activos", required=False, initial=True)


class ClienteTable(Table):
    class Meta:
        attrs = {"id": "clientes-table"}
        model = Cliente
        per_page = 30
        fields = ("tipo_doc", "nro_doc", "nombre", "condicion_iva", "domicilio", "localidad", "email", "activo")
        template = 'empresa/table.html'

    domicilio = Column(visible=False)
    telefono = Column(visible=False)
    email = Column(visible=False)

    actions = EditColumn('cliente.update', kwargs={"pk": A('pk')}, orderable=False, accessor='pk',
                         verbose_name="Acciones")
    delete = DeleteColumn('cliente.delete', kwargs={"pk": A('pk')}, orderable=False, accessor='pk', verbose_name=" ")


class ClienteList(SingleTableView):
    model = Cliente
    table_class = ClienteTable

    def get(self, request, *args, **kwargs):
        self.form = ClienteSearchForm(self.request.GET or None)
        if not self.request.GET or self.form.is_valid():
            return super(ClienteList, self).get(request, *args, **kwargs)
        else:
            return HttpResponseBadRequest()

    def get_queryset(self):
        queryset = super(ClienteList, self).get_queryset()
        if hasattr(self.form, "cleaned_data"):
            if self.form.cleaned_data["nombre"]:
                queryset = queryset.filter(nombre__icontains=self.form.cleaned_data["nombre"])
            if self.form.cleaned_data["doc"]:
                queryset = queryset.filter(
                    nro_doc__iexact=self.form.cleaned_data["doc"].strip().replace("-", "").replace(".", ""))
            if self.form.cleaned_data["activo"]:
                queryset = queryset.filter(activo=self.form.cleaned_data["activo"])
            queryset = queryset.filter(editable=True).order_by("-activo", "nombre", "-pk")
            # queryset = queryset.filter(editable=True).order_by("nombre", "-pk")
        else:
            queryset = queryset.filter(editable=True, activo=True).order_by("-activo", "nombre", "-pk")
            # queryset = queryset.filter(editable=True).order_by("nombre", "-pk")
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ClienteList, self).get_context_data(**kwargs)
        context['form'] = self.form
        return context

    def get_table(self):
        table = super(ClienteList, self).get_table()
        table_exclude = ()
        if not (self.request.user.has_perm("empresa.change_cliente")):
            table_exclude += ('actions',)
        if not (self.request.user.has_perm("empresa.delete_cliente")):
            table_exclude += ('delete',)
        table.exclude = table_exclude
        return table

cliente_list = login_required(ClienteList.as_view())


class ClienteCreate(CreateView):
    model = Cliente
    form_class = ClienteForm
    success_url = reverse_lazy('cliente.list')

    @method_decorator(permission_required("empresa.add_cliente", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ClienteCreate, self).dispatch(*args, **kwargs)


cliente_create = login_required(ClienteCreate.as_view())


class ClienteUpdate(MessageUpdateView):
    model = Cliente
    form_class = ClienteForm
    success_url = reverse_lazy('cliente.list')

    @method_decorator(permission_required("empresa.change_cliente", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        if self.request.user.has_perm("empresa.change_cliente"):
            return super(ClienteUpdate, self).dispatch(*args, **kwargs)
        messages.error(self.request,
                        'Su usuario con los permisos necesarios para realizar esta accion.')
        return HttpResponseRedirect(reverse_lazy('cliente.list'))

    def get_queryset(self):
        return Cliente.objects.filter(editable=True).all()


cliente_update = login_required(ClienteUpdate.as_view())


class ClienteDelete(DeleteView):
    model = Cliente
    success_url = reverse_lazy('cliente.list')

    @method_decorator(permission_required("empresa.delete_cliente", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ClienteDelete, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClienteDelete, self).get_context_data(**kwargs)
        context['cant_comp_asociados'] = Comprobante.objects.filter(cliente=self.object).count()
        context['entidad_a_borrar'] = "cliente"
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.activo:
            self.object.activo = False
            self.object.fecha_baja = datetime.date.today()
            self.object.usuario_baja = request.user
        else:
            self.object.activo = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


cliente_delete = login_required(ClienteDelete.as_view())


class ProductoForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ["codigo", "codigo_barras_nro", "nombre", "ingresa_precio_final", "precio_final", "precio_unit",
                  "alicuota_iva", "unidad"]
        model = Producto

    ingresa_precio_final = forms.BooleanField(label="Preferís ingresar precio final?", required=False)
    alicuota_iva = forms.ModelChoiceField(queryset=AlicuotaIva.objects.order_by("id_afip"), required=False,
                                          widget=SelectAlicuotaIva, empty_label=None)
    codigo_barras_nro = forms.DecimalField(label="Codigo de barras (EAN)", max_digits=13, decimal_places=0,
                                           required=False)
    precio_final = forms.DecimalField(label="Precio final (con IVA)", max_digits=19, decimal_places=4, required=False)
    precio_unit = forms.DecimalField(label="Precio unitario (sin IVA)", max_digits=19, decimal_places=4)
    unidad = forms.ModelChoiceField(queryset=Unidad.objects.exclude(id_afip=Unidad.BONIFICACION_ID_AFIP), required=True)


class ProductoTable(Table):
    class Meta:
        attrs = {"id": "productos-table"}
        model = Producto
        per_page = 30
        fields = (
        "codigo", "codigo_barras_nro", "nombre", "unidad", "precio_unit", "precio_final", "alicuota_iva", "activo")

    actions = EditColumn('producto.update', kwargs={"pk": A('pk')}, orderable=False, accessor='pk',
                         verbose_name="Acciones")
    delete = DeleteColumn('producto.delete', kwargs={"pk": A('pk')}, orderable=False, accessor='pk', verbose_name=" ")
    codigo_barras_nro = Column(verbose_name="Codigo de barras")
    precio_unit = MoneyColumn()
    precio_final = MoneyColumn(orderable=False)


class ProductoSearchForm(Form):
    nombre = forms.CharField(label="Nombre", required=False)
    codigo = forms.CharField(label="Código", required=False)
    codigo_barras_nro = forms.CharField(label="Código de barras", required=False)
    activo = forms.BooleanField(label="Solo activos", required=False, initial=True)


class ProductoList(SingleTableView):
    model = Producto
    table_class = ProductoTable

    def get(self, request, *args, **kwargs):
        self.form = ProductoSearchForm(self.request.GET or None)
        if not self.request.GET or self.form.is_valid():
            return super(ProductoList, self).get(request, *args, **kwargs)
        else:
            return HttpResponseBadRequest()

    def get_queryset(self):
        queryset = super(ProductoList, self).get_queryset()
        if hasattr(self.form, "cleaned_data"):
            if self.form.cleaned_data["nombre"]:
                queryset = queryset.filter(nombre__icontains=self.form.cleaned_data["nombre"])
            if self.form.cleaned_data["codigo"]:
                queryset = queryset.filter(codigo__iexact=self.form.cleaned_data["codigo"])
            if self.form.cleaned_data["codigo_barras_nro"]:
                queryset = queryset.filter(codigo_barras_nro__icontains=self.form.cleaned_data["codigo_barras_nro"])
            if self.form.cleaned_data["activo"]:
                queryset = queryset.filter(activo=self.form.cleaned_data["activo"])
            queryset = queryset.order_by("-activo", "codigo", "nombre", "-pk")
            # queryset = queryset.order_by("codigo", "nombre", "-pk")
        else:
            queryset = queryset.filter(activo=True).order_by("-activo", "codigo", "nombre", "-pk")
            # queryset = queryset.order_by("codigo", "nombre", "-pk")
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProductoList, self).get_context_data(**kwargs)
        context['form'] = self.form
        return context
    
    def get_table(self):
        table = super(ProductoList, self).get_table()
        table_exclude = ()
        if not (self.request.user.has_perm("empresa.change_producto")):
            table_exclude += ('actions',)
        if not (self.request.user.has_perm("empresa.delete_producto")):
            table_exclude += ('delete',)
        table.exclude = table_exclude
        return table


producto_list = login_required(ProductoList.as_view())


class ProductoCreate(CreateView):
    model = Producto
    form_class = ProductoForm
    success_url = reverse_lazy('producto.list')

    # @method_decorator(permission_required("empresa.add_producto", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        if self.request.user.has_perm("empresa.add_producto"):
            return super(ProductoCreate, self).dispatch(*args, **kwargs)
        messages.error(self.request,
                        'Su usuario con los permisos necesarios para realizar esta accion.')
        return HttpResponseRedirect(reverse_lazy('producto.list'))

producto_create = login_required(ProductoCreate.as_view())


class ProductoUpdate(MessageUpdateView):
    model = Producto
    form_class = ProductoForm
    success_url = reverse_lazy('producto.list')

    @method_decorator(permission_required("empresa.change_producto", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        if self.request.user.has_perm("empresa.change_producto"):
            return super(ProductoUpdate, self).dispatch(*args, **kwargs)
        messages.error(self.request,
                        'Su usuario con los permisos necesarios para realizar esta accion.')
        return HttpResponseRedirect(reverse_lazy('producto.list'))


producto_update = login_required(ProductoUpdate.as_view())


class ProductoDelete(DeleteView):
    model = Producto
    success_url = reverse_lazy('producto.list')

    @method_decorator(permission_required("empresa.delete_producto", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ProductoDelete, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProductoDelete, self).get_context_data(**kwargs)
        context['cant_comp_asociados'] = DetalleComprobante.objects.filter(producto=self.object).order_by(
            'comprobante_id').distinct('comprobante_id').count()
        context['entidad_a_borrar'] = "producto"
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.activo:
            self.object.activo = False
            self.object.fecha_baja = datetime.date.today()
            self.object.usuario_baja = request.user
        else:
            self.object.activo = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


producto_delete = login_required(ProductoDelete.as_view())

INCREMENTAR_CHOICES = ('1', 'Incrementar',), ('0', 'Decrementar',)


class ProductoCambiarPreciosForm(Form):
    porcentaje = forms.IntegerField(required=True)
    incrementar = forms.ChoiceField(widget=forms.RadioSelect,
                                    choices=INCREMENTAR_CHOICES,
                                    initial='1',
                                    label="")


@csrf_exempt
@login_required
@permission_required('empresa.change_producto', raise_exception=True)
def change_prices(request):
    form_precios = ProductoCambiarPreciosForm()
    if request.method == 'POST':
        form_masivo = ProductoCambiarPreciosForm(request.POST)
        if form_masivo.is_valid():
            try:
                incrementar = bool(int(form_masivo.cleaned_data["incrementar"]))
                porcentaje = Decimal(form_masivo.cleaned_data["porcentaje"])
                if porcentaje <= 0:
                    messages.error(request, "El porcentaje debe ser un numero positivo.")
                    return HttpResponseRedirect(reverse_lazy('producto.list'))

                productos = Producto.objects.filter(activo=True)
                if not productos:
                    messages.error(request, "No hay productos para actualizar.")
                    return HttpResponseRedirect(reverse_lazy('producto.list'))

                if incrementar:
                    multiplicador = (1 + (porcentaje / 100))
                else:
                    multiplicador = (1 - (porcentaje / 100))

                productos.update(precio_unit=F('precio_unit') * multiplicador)

                messages.success(request, 'Se actualizaron con éxito {} productos.'.format(productos.count()))

                return HttpResponseRedirect(reverse_lazy('producto.list'))
            except Exception as e:
                messages.error(request, str(e))
                return HttpResponseRedirect(reverse_lazy('producto.list'))
        else:
            messages.error(request, "Hay errores en el formulario. Por favor, corríjalos y vuelva a intentarlo.")
            return HttpResponseRedirect(reverse_lazy('producto.list'))
    else:
        return render_to_response('empresa/modificar_precios.html', {"form": form_precios},
                                  RequestContext(request))


class ProductImportForm(Form):
    file = FileField(required=True, label='Archivo - Seleccione el archivo csv que contiene los productos a importar')
    update_existing = forms.BooleanField(required=False,
                                         label='Actualizar los productos que ya existan en Pirra')
    is_final_price = forms.BooleanField(required=False, label='Los productos a importar incluyen IVA')
    exclude_first_line = forms.BooleanField(initial=True, required=False,
                                            label='Excluir la primera línea (encabezado de columnas)')

    def __init__(self, *args, **kwargs):
        super(ProductImportForm, self).__init__(*args, **kwargs)
        self.fields[
            'is_final_price'].help_text = 'Si no incluye la Alícuota de IVA que le corresponde al producto se completará con el 21% por definición.'
        self.fields[
            'update_existing'].help_text = 'Si no tilda esta opción, los productos a importar que ya existan en el sistema serán ignorados.'

    def save(self):
        update_existing = self.cleaned_data["update_existing"]
        exclude_first_line = self.cleaned_data["exclude_first_line"]
        is_final_price = self.cleaned_data["is_final_price"]
        StreamReader = codecs.getreader('utf-8')
        file = StreamReader(self.cleaned_data["file"])
        errors, imported, ignored, updated = import_product_csv(file, update_existing, exclude_first_line,
                                                                is_final_price)
        if errors:
            for err in errors:
                self.add_error(None, err)
        return errors, imported, ignored, updated

@login_required()
@permission_required('empresa.add_producto', raise_exception=True)
def import_product(request):
    if request.method == 'POST':
        form = ProductImportForm(request.POST, request.FILES)
    else:
        form = ProductImportForm()

    if form.is_valid():
        display_message = ""
        error = False

        try:
            errors, imported, ignored, updated = form.save()
        except Exception as e:
            display_message += "Error: {}".format(str(e))
            error = True

        if not (error or errors):
            if imported > 0 or updated > 0 and not errors:
                display_message += "Importación masiva realizada con éxito."
                result_type = 'success'
            else:
                display_message += "No se encontraron productos para importar."
                result_type = 'warning'

            result = {
                'imported': str(imported),
                'ignored': str(ignored),
                'updated': str(updated),
                'result': display_message,
                'result_type': result_type
            }
            return render(request, 'empresa/importacion_success.html',
                                      {"result": result,
                                       "entity": "producto"})

    return render(request, 'empresa/producto_importacion.html', {"form": form})

class ClientImportForm(Form):
    file = FileField(required=True, label='Archivo - Seleccione el archivo csv que contiene los clientes a importar')
    update_existing = forms.BooleanField(required=False, label='Actualizar los clientes que ya existan en Pirra')
    exclude_first_line = forms.BooleanField(initial=True, required=False,
                                            label='Excluir la primera línea (encabezado de columnas)')

    def __init__(self, *args, **kwargs):
        super(ClientImportForm, self).__init__(*args, **kwargs)
        self.fields[
            'update_existing'].help_text = 'Si no tilda esta opción, los clientes a importar que ya existan en el sistema serán ignorados.'

    def save(self):
        update_existing = self.cleaned_data["update_existing"]
        exclude_first_line = self.cleaned_data["exclude_first_line"]
        StreamReader = codecs.getreader('utf-8')
        file = StreamReader(self.cleaned_data["file"])
        errors, imported, ignored, updated = import_client_csv(file, update_existing, exclude_first_line)
        if errors:
            for err in errors:
                self.add_error(None, err)
        return errors, imported, ignored, updated


@login_required()
@permission_required('empresa.add_cliente', raise_exception=True)
def import_client(request):
    if request.method == 'POST':
        form = ClientImportForm(request.POST, request.FILES)
    else:
        form = ClientImportForm()

    if form.is_valid():
        display_message = ""
        error = False

        try:
            errors, imported, ignored, updated = form.save()
        except Exception as e:
            display_message += "Error: {}".format(str(e))
            error = True

        if not (error or errors):
            if imported > 0 or updated > 0 and not errors:
                display_message += "Importación masiva realizada con éxito."
                result_type = 'success'
            else:
                display_message += "No se encontraron clientes para importar."
                result_type = 'warning'

            result = {
                'imported': str(imported),
                'ignored': str(ignored),
                'updated': str(updated),
                'result': display_message,
                'result_type': result_type
            }
            return render(request, 'empresa/importacion_success.html',
                                      {"result": result,
                                       "entity": "cliente"})

    return render(request, "empresa/cliente_importacion.html",
                              {"form": form})
