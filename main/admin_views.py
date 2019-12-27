from collections import OrderedDict

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.urls import reverse_lazy
from rest_framework.authtoken.models import Token

from afip.models import TipoComprobante
from comprobante.vendor.pyafipws.ws import ws_helper


def consultar_comprobante(request):
    if request.POST and all (k in list(request.POST.keys()) for k in ('cuit','tipo_cbte','punto_vta','nro')):
        try:
            ret = ws_helper.consultar_comprobante(
                settings.CERTIFICATE,
                settings.PRIVATE_KEY,
                request.POST['cuit'],
                request.POST['tipo_cbte'],
                request.POST['punto_vta'],
                request.POST['nro']
            )
            return render_to_response('admin/consultar_comprobante.html', {"comprobante": ret}, RequestContext(request))
        except Exception as e:
            tipos_cbte = TipoComprobante.objects.all()
            return render_to_response('admin/consultar_comprobante.html', {"tipos_cbte": tipos_cbte, "error": e}, RequestContext(request))
    else:
        tipos_cbte = TipoComprobante.objects.all()
        return render_to_response('admin/consultar_comprobante.html', {"tipos_cbte": tipos_cbte}, RequestContext(request))


class TokenUserForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ["email"]

    def clean_username(self):
        return self.cleaned_data["username"].lower()

    def __init__(self, *args, **kwargs):
        super(TokenUserForm, self).__init__(*args, **kwargs)
        self.fields = OrderedDict((k, self.fields[k]) for k in ["username", "email"])
        self.fields['username'].help_text = ''
        self.fields['username'].label = 'Username '

    email = forms.EmailField(label='Email ', max_length=100)

    def save(self, commit=True):
        user = super(TokenUserForm, self).save(commit=False)
        if commit:
            user.save()
        return user


def tokens_admin(request):
    if request.POST:
        form_user = TokenUserForm(request.POST)
        if form_user.is_valid():
            try:
                user = form_user.save(commit=False)
                user.username = form_user.clean_username()
                user.email = form_user.cleaned_data["email"]
                user.save()
            except:
                raise

            Token.objects.create(user=user)
        else:
            return render_to_response('admin/tokens_admin.html', {"form_user": form_user}, RequestContext(request))

    tokens = Token.objects.all()
    users_without_token = User.objects.filter(auth_token__isnull=True)

    form_user = TokenUserForm()

    return render_to_response('admin/tokens_admin.html',
                              {"tokens": tokens,
                               "users_without_token": users_without_token,
                               "form_user": form_user,
                               }, RequestContext(request))


def create_token(request):
    user_id = request.POST['user_id']
    user = User.objects.get(pk=user_id)
    Token.objects.create(user=user)
    return HttpResponseRedirect(reverse_lazy('admin.tokens_admin'))


def delete_token(request):
    user_id = request.POST['user_id']
    Token.objects.get(user_id=user_id).delete()
    return HttpResponseRedirect(reverse_lazy('admin.tokens_admin'))    