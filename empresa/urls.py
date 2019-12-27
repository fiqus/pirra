from django.urls import path, re_path

from . import views

urlpatterns = [
    path('empresa', views.empresa_update, name='empresa.update'),

    path('users', views.user_list, name='user.list'),
    path('users/create', views.user_create, name='user.create'),
    re_path(r'^users/update/(?P<pk>\d+)', views.user_update, name='user.update'),

    # url(r'^groups$', views.group_list, name='group.list'),
    # url(r'^groups/create', views.group_create, name='group.create'),
    # url(r'^groups/update/(?P<pk>\d+)', views.group_update, name='group.update'),

    path('puntos_de_venta', views.punto_de_venta_list, name='punto_de_venta.list'),
    path('puntos_de_venta/create', views.punto_de_venta_create, name='punto_de_venta.create'),
    re_path(r'^puntos_de_venta/update/(?P<pk>\d+)', views.punto_de_venta_update, name='punto_de_venta.update'),
    re_path(r'^puntos_de_venta/delete/(?P<pk>\d+)', views.punto_de_venta_delete, name='punto_de_venta.delete'),
    path('puntos_de_venta/get_ptos_venta_afip', views.get_ptos_venta_afip, name='punto_de_venta.get_ptos_venta_afip'),

    path('clientes', views.cliente_list, name='cliente.list'),
    path('clientes/create', views.cliente_create, name='cliente.create'),
    re_path(r'^clientes/update/(?P<pk>\d+)', views.cliente_update, name='cliente.update'),
    re_path(r'^clientes/delete/(?P<pk>\d+)', views.cliente_delete, name='cliente.delete'),
    path('clientes/import/', views.import_client, name='cliente.import_client'),

    path('productos', views.producto_list, name='producto.list'),
    path('productos/create', views.producto_create, name='producto.create'),
    re_path(r'^productos/update/(?P<pk>\d+)', views.producto_update, name='producto.update'),
    re_path(r'^productos/delete/(?P<pk>\d+)', views.producto_delete, name='producto.delete'),
    path('productos/change_prices', views.change_prices, name='producto.change_prices'),
    path('productos/import/', views.import_product, name='producto.import_product'),
]
