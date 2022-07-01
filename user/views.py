from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.forms import ModelForm, CharField, TextInput, ModelMultipleChoiceField, CheckboxSelectMultiple
from django.shortcuts import render, redirect

from afip.models import TipoComprobante, ResolucionGeneral
from empresa.models import Empresa
from empresa.views import ImagePreviewWidget
from user.models import ProxiUser


class CreateUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    dni = forms.CharField(max_length=100, required=True, label="Dni")
    company = forms.ModelChoiceField(queryset=Empresa.objects.all(), required=False, label="Empresa")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'groups')

    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), widget=forms.CheckboxSelectMultiple(), label="Permisos")


def create_user(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            dni = form.cleaned_data.get('dni')
            company_name = form.cleaned_data.get('company')
            company = Empresa.objects.get(nombre=company_name)
            user = authenticate(username=username, password=raw_password)
            user.groups.set(form.cleaned_data["groups"])
            ProxiUser.objects.create(user=user, dni=dni, company=company)
            login(request, user)
            return redirect("index")
    else:
        form = CreateUserForm()
    return render(request, 'create_user_form.html', {'form': form})


class CompanyForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(CompanyForm, self).__init__(*args, **kwargs)
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

    nro_doc = CharField(max_length=100)
    tipos_cbte = ModelMultipleChoiceField(queryset=TipoComprobante.objects.all(),
                                          widget=CheckboxSelectMultiple)

    resoluciones_generales = ModelMultipleChoiceField(queryset=ResolucionGeneral.objects.all(), required=False,
                                                      widget=CheckboxSelectMultiple)
    nombre = forms.CharField(max_length=100)
    logo = forms.ImageField(widget=ImagePreviewWidget, required=False)


def create_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("create_user")
    else:
        form = CompanyForm()
    return render(request, 'create_company_form.html', {'form': form})
