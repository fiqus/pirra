from django.contrib import admin
from comprobante.models import Comprobante, DetalleComprobante
from django.http import HttpResponseRedirect
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.contrib.postgres.fields.jsonb import KeyTextTransform

admin.register(Comprobante)
admin.register(DetalleComprobante)

def fix_jsondata(comprobante):
    comprobante.set_json_data()
    comprobante.data_arreglada = True
    comprobante.save()

@admin.register(Comprobante)
class ComprobanteAdmin(admin.ModelAdmin):
    fields = (
        'tipo_cbte', 'cliente', 'nro', 'fecha_emision', 'cae', 'data'
    )
    readonly_fields = (
        'tipo_cbte', 'cliente', 'nro', 'fecha_emision', 'cae', 'data'
    )
    list_display = (
        'tipo_cbte', 'cliente', 'nro', 'nro_data', 'fecha_emision', 'fecha_emision_data', 'cae', 'cae_data', 'data_arreglada'
    )
    actions = None
    change_form_template = "comprobante/admin/comprobante_fix_jsondata.html"

    def nro_data(self, instance):
        if instance.data is None:
            return "NO_DATA"
        return instance.data["nro"]

    def fecha_emision_data(self, instance):
        if instance.data is None:
            return "NO_DATA"
        return instance.data["fecha_emision"]

    def cae_data(self, instance):
        if instance.data is None:
            return "NO_DATA"
        return instance.data["cae"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def response_change(self, request, obj):
        if not request.user.is_superuser:
            self.message_user(request, "Que hace papi?")
            return HttpResponseRedirect(".")

        if "_fix-jsondata" in request.POST:
            fix_jsondata(obj)
            self.message_user(request, "Comprobante actualizado correctamente")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    # filtra comprobantes cuyo json_data esta vacio "O" los comprobantes cuyo cae es distinto del cae en el json_data
    def get_queryset(self, request):
        qs = super(ComprobanteAdmin, self).get_queryset(request)
        # KeyTextTransform extrae el campo 'cae' del json 'data'
        # Cast castea el campo extraido a un CharField
        return qs.filter(Q(data__isnull=True) | ~Q(cae=Cast(KeyTextTransform('cae', 'data'), output_field=CharField())) | Q(data_arreglada=True))