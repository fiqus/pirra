from django.urls import path, re_path

from comprobante.views.cbte_autorizar import comprobante_autorizar, comprobante_autorizar_masivo, \
    comprobante_autorizar_masivo_seleccion
from comprobante.views.cbte_create_edit import comprobante_create_edit
from comprobante.views.cbte_delete import comprobante_delete
from comprobante.views.cbte_duplicar import comprobante_duplicate, comprobante_duplicar_masivo_seleccion
from comprobante.views.cbte_export import comprobante_exportar_masivo
from comprobante.views.cbte_import import cbte_import
from comprobante.views.cbte_imprimir import comprobante_imprimir_masivo, comprobante_imprimir_masivo_seleccion
from comprobante.views.cbte_list import comprobante_list
from comprobante.views.cbte_list_extra_functions import comprobante_eliminar_masivo, \
    comprobante_eliminar_masivo_seleccion, comprobante_enviar_masivo_seleccion, get_porcentaje_impuesto, enviar_factura, \
    enviar_comp_mail, cliente_list_dialog, cliente_new_dialog, check_status, exportar_citi_ventas, generar_citi_ventas, \
    historial_envios
from comprobante.views.cbte_pdf import comprobante_to_pdf
from comprobante.views.cbte_preview import comprobante_preview
from . import views

urlpatterns = [
    path('', comprobante_list, name='comprobante.list'),
    path('create', comprobante_create_edit, name='comprobante.create'),
    re_path(r'^duplicate/(?P<pk>\d+)$', comprobante_duplicate, name='comprobante.duplicate'),
    path('import', cbte_import, name='comprobante.import'),
    re_path('^edit/(?P<pk>\d+)$', comprobante_create_edit, name='comprobante.edit'),
    re_path(r'^create_from_oc/(?P<pk_comprobante_na>\d+)$', comprobante_create_edit, name='comprobante.create_from_oc'),
    re_path(r'^delete/(?P<pk>\d+)$', comprobante_delete, name='comprobante.delete'),
    re_path(r'^preview/(?P<pk>\d+)$', comprobante_preview, name='comprobante.preview'),
    re_path(r'^autorizar/(?P<pk>\d+)$', comprobante_autorizar, name='comprobante.autorizar'),
    path('autorizar_masivo/', comprobante_autorizar_masivo, name='comprobante.autorizar_masivo'),
    path('autorizar_masivo_seleccion/', comprobante_autorizar_masivo_seleccion, name='comprobante.autorizar_masivo_seleccion'),
    path('duplicar_masivo_seleccion/', comprobante_duplicar_masivo_seleccion, name='comprobante.duplicar_masivo_seleccion'),
    path('imprimir_masivo/', comprobante_imprimir_masivo, name='comprobante.imprimir_masivo'),
    path('imprimir_masivo_seleccion/', comprobante_imprimir_masivo_seleccion, name='comprobante.imprimir_masivo_seleccion'),
    path('eliminar_masivo/', comprobante_eliminar_masivo, name='comprobante.eliminar_masivo'),
    path('eliminar_masivo_seleccion/', comprobante_eliminar_masivo_seleccion, name='comprobante.eliminar_masivo_seleccion'),
    path('enviar_masivo_seleccion/', comprobante_enviar_masivo_seleccion, name='comprobante.enviar_masivo_seleccion'),
    re_path(r'^print/(?P<pk>\d+)$', comprobante_to_pdf, name='comprobante.imprimir'),
    re_path(r'^get_porcentaje_impuesto/(?P<pk>\d+)$', get_porcentaje_impuesto, name='comprobante.get_porcentaje_impuesto'),
    path('get_porcentaje_impuesto/', get_porcentaje_impuesto, name='comprobante.get_porcentaje_impuesto'),
    path('enviar/', enviar_factura, name='comprobante.enviar'),
    re_path(r'^enviar_comp_mail/(?P<pk>\d+)$', enviar_comp_mail, name='comprobante.enviar_comp_mail'),
    path('listado_clientes/', cliente_list_dialog, name='comprobante.listado_clientes'),
    path('new_cliente/', cliente_new_dialog, name='comprobante.new_cliente'),
    path('comprobante/check_status/', check_status, name='comprobante.check_status'),
    path('exportar_citi_ventas/', exportar_citi_ventas, name='comprobante.exportar_citi_ventas'),
    path('exportar_masivo/', comprobante_exportar_masivo, name='comprobante.exportar_masivo'),
    path('generar_citi_ventas/', generar_citi_ventas, name='comprobante.generar_citi_ventas'),
    re_path(r'^historial_envios/(?P<pk>\d+)$', historial_envios, name='comprobante.historial_envios'),
]
