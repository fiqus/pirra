from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from empresa.views import punto_de_venta_list
from hooks.decorators import hook_receiver


@hook_receiver("pirra.template.nav")
def add_nav(context, *args, **kwargs):
    return render_to_string("sample_hooks/extra_nav.html")


@hook_receiver("hooks.process_view")
def redirect(request, view_func, view_args, view_kwargs):
    if view_func == punto_de_venta_list:
        return HttpResponseRedirect("/")

@hook_receiver("pirra.template.alerts")
def add_message(context, *args, **kwargs):
    return mark_safe("<div class='alert alert-warning' role='alert'>Sample warning alert!</div>")