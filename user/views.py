from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django import forms
from django.contrib.auth.models import User, Group

from empresa.models import Empresa
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
