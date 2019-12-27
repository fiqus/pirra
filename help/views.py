from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db import connection
from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import render_to_response
# Create your views here.
from django.template.context import Context, RequestContext
from django.template.loader import get_template
from django.views.generic import ListView, FormView
from django_tables2 import Table

from afip.models import TipoComprobante, Concepto, TipoDoc, TipoExportacion, Moneda, Idioma, Incoterms, PaisDestino, \
    CondicionVenta, Unidad, AlicuotaIva, CondicionIva, Tributo, Opcional
from help.models import FrequentlyAskedQuestion


class FAQList(ListView):
    model = FrequentlyAskedQuestion

    queryset = FrequentlyAskedQuestion.objects.filter(published=True)


faqs = login_required(FAQList.as_view())


class ContactForm(Form):
    name = forms.CharField(label="Nombre")
    email = forms.EmailField(label="E-Mail")
    message = forms.CharField(label="Mensaje", widget=forms.Textarea)


def send_contact_message(template, context, subject, email, reply_to):
    plaintext = get_template(template + '.txt')
    html_template = get_template(template + '.html')

    text_content = plaintext.render(context)
    html_content = html_template.render(context)

    mail = EmailMultiAlternatives(subject, text_content,
                                  settings.DEFAULT_FROM_EMAIL, [email],
                                  headers={'Reply-To': reply_to, "X-Mailin-tag": "contacto_cliente"})

    mail.attach_alternative(html_content, "text/html")
    mail.send()


class Contact(FormView):
    template_name = 'contact_form.html'
    form_class = ContactForm

    def form_invalid(self, form):
        response = super(Contact, self).form_invalid(form)
        response.status_code = 400
        return response

    def form_valid(self, form):

        d = Context({
            'message': form.cleaned_data["message"],
            'name': form.cleaned_data["name"],
            'email': form.cleaned_data["email"],
            'client_name': connection.tenant.name
        })

        # Mail para el equipo desarrollo de Pirra
        send_contact_message('contact_email',
                             d,
                             "[Pirra] - Consulta de Cliente {}".format(connection.tenant.name),
                             settings.CONTACT_EMAIL,
                             form.cleaned_data["email"])

        # Mail de confirmacion al usuario que mando el contacto
        send_contact_message('contact_confirmation_email',
                             d,
                             "[Pirra] - Su consulta ha sido recibida",
                             form.cleaned_data["email"],
                             form.cleaned_data["email"])

        return HttpResponse()

    def get_initial(self):
        return {
            "name": self.request.user.get_full_name() or self.request.user.username,
            "email": self.request.user.email
        }


contact_view = login_required(Contact.as_view())


def get_table(klass, include_fields):
    class T(Table):
        class Meta:
            model = klass
            fields = include_fields
            order_by = include_fields

    return T(klass.objects.all())


def dev_help(request):
    params = {
        'valid_param_values': [
            {"title": "Tipos de Comprobante",
             "values": get_table(TipoComprobante, ('id_afip', 'nombre', 'letra'))},
            {"title": "Conceptos",
             "values": get_table(Concepto, ('id_afip', 'nombre'))},
            {"title": "Tipos de documento",
             "values": get_table(TipoDoc, ('id_afip', 'nombre'))},
            {"title": "Tipos de exportacion",
             "values": get_table(TipoExportacion, ('id_afip', 'nombre'))},
            {"title": "Monedas",
             "values": get_table(Moneda, ('id_afip', 'nombre'))},
            {"title": "Idiomas",
             "values": get_table(Idioma, ('id_afip', 'nombre'))},
            {"title": "Incoterms",
             "values": get_table(Incoterms, ('id_afip', 'nombre'))},
            {"title": "Paises de destino",
             "values": get_table(PaisDestino, ('id_afip', 'nombre', 'cuit'))},
            {"title": "Condiciones de Venta",
             "values": get_table(CondicionVenta, ('id', 'nombre'))},
            {"title": "Unidades de Medida",
             "values": get_table(Unidad, ('id_afip', 'nombre'))},
            {"title": "Alicuotas IVA.",
             "values": get_table(AlicuotaIva, ('id_afip', 'nombre', 'porc'))},
            {"title": "Condiciones de IVA.",
             "values": get_table(CondicionIva, ('id_afip', 'nombre'))},
            {"title": "Tributos",
             "values": get_table(Tributo, ('id_afip', 'nombre'))},
            {"title": "Opcionales",
             "values": get_table(Opcional, ('id_afip', 'resolucion_general', 'campo'))},
        ]}
    return render_to_response("help/dev_help.html", params, RequestContext(request))


def help_edi(request):
    return render_to_response("edi/help_edi.html", RequestContext(request))
