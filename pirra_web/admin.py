from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.contrib.admin import ModelAdmin

from afip.models import CondicionIIBB, CondicionIva, Idioma, AlicuotaIva, Incoterms, Moneda, PaisDestino, \
    TipoComprobante, TipoComprobanteAlicuotaIva, Unidad, TipoExportacion, TipoDoc, CondicionVenta, Padron, Tributo, \
    ResolucionGeneral, Opcional, OpcionOpcional
from help.models import FrequentlyAskedQuestion, LatestNews
from main.admin_views import consultar_comprobante, tokens_admin, create_token, delete_token
from user.models import ProxiUser

admin.site.register(CondicionIIBB)
admin.site.register(CondicionIva)
admin.site.register(Idioma)
admin.site.register(AlicuotaIva)
admin.site.register(Incoterms)
admin.site.register(Moneda)
admin.site.register(PaisDestino)
admin.site.register(TipoComprobante)
admin.site.register(TipoComprobanteAlicuotaIva)
admin.site.register(Unidad)
admin.site.register(TipoExportacion)
admin.site.register(TipoDoc)
admin.site.register(CondicionVenta)
admin.site.register(Padron)
admin.site.register(LatestNews)
admin.site.register(Tributo)
admin.site.register(ResolucionGeneral)
admin.site.register(Opcional)
admin.site.register(OpcionOpcional)
admin.site.register(ProxiUser)


class MyModelAdmin(SortableAdminMixin, ModelAdmin):
    pass


admin.site.register(FrequentlyAskedQuestion, MyModelAdmin)

# admin.site.register_view('consultar_comprobante/', urlname='consultar_comprobante', view=consultar_comprobante)
#
# admin.site.register_view('tokens_admin/', urlname='tokens_admin', view=tokens_admin)
# admin.site.register_view('tokens_admin/create_token/', urlname='create_token', view=create_token)
# admin.site.register_view('tokens_admin/delete_token/', urlname='delete_token', view=delete_token)
