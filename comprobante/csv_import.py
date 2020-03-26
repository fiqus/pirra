# -*- coding: utf-8 -*-
import csv
import datetime
from decimal import Decimal
import logging
from django.db import transaction
from afip.models import TipoComprobante, Concepto, TipoDoc, TipoExportacion, Moneda, Idioma, Incoterms, PaisDestino, \
    CondicionVenta, Unidad, AlicuotaIva, CondicionIva, Tributo, Opcional
from comprobante.models import Comprobante, DetalleComprobante, TributoComprobante, OpcionalComprobante
from empresa.models import PuntoDeVenta, Empresa, Cliente, Producto

logger = logging.getLogger(__name__)

prod_import_fields = [
    "prod_item_number",  # un nro distinto para cada cbte, no se guarda
    "prod_codigo",  # codigo
    "prod_nombre",
    "prod_precio_unit",
    "prod_alicuota_iva", #id_afip, tiene que estar cargado
    "prod_unidad", #id_afip, tiene que estar cargado
    "prod_codigo_barras",  # codigo de barras EAN
]


cli_import_fields = [
    "cli_item_number",  # un nro distinto para cada cbte, no se guarda
    "cli_tipo_doc",
    "cli_nro_doc",
    "cli_nombre",
    "cli_condicion_iva",
    "cli_domicilio",
    "cli_localidad",
    "cli_telefono",
    "cli_cod_postal",
    "cli_email",
]

cbte_import_fields = [
    "cbte_item_number",  # un nro distinto para cada cbte, no se guarda
    "cbte_tipo_cbte",  # id_afip, tiene que estar cargado
    "cbte_punto_vta",  # id_afip, tiene que estar cargado
    "cbte_concepto",  # id_afip, tiene que estar cargado
    "cbte_nro_remito",  # opcional, max_length=13
    "cbte_fecha_emision",  # formato DD/MM/YYYY datetime.datetime.strptime('05/07/2015', '%d/%m/%Y').date()
    "cbte_fecha_vencimiento",  # formato DD/MM/YYYY datetime.datetime.strptime('05/07/2015', '%d/%m/%Y').date()
    "cbte_id_tipo_doc_cliente",  # id_afip, tiene que estar cargado
    "cbte_nro_doc_cliente",  # si no esta en el sistema lo crea...?
    "cbte_cliente_nombre",  # opcional, solo si el cliente no esta en el sistema
    "cbte_cliente_condicion_iva",  # ID afip, opcional, solo si el cliente no esta en el sistema
    "cbte_cliente_domicilio",  # opcional, solo si el cliente no esta en el sistema
    "cbte_cliente_localidad",  # opcional, solo si el cliente no esta en el sistema
    "cbte_cliente_telefono",  # opcional, solo si el cliente no esta en el sistema
    "cbte_cliente_cp",
    "cbte_cliente_email",
    "cbte_tipo_exportacion",  # opcional, id_afip, tiene que estar cargado
    "cbte_id_moneda",  # id_afip, tiene que estar cargado default PES
    "cbte_moneda_ctz",  # opcional, default 1
    "cbte_id_idioma",  # opcional, default 1
    "cbte_id_incoterms",  # opcional, id_afip, tiene que estar cargado
    "cbte_incoterms_ds",  # opcional
    "cbte_id_pais_destino",  # opcional, id_afip, tiene que estar cargado
    "cbte_id_impositivo",  # opcional, no se que es, jaja  max_length=256
    "cbte_observaciones_comerciales",  # texto libre
    "cbte_observaciones",  # texto libre
    "cbte_forma_pago",  # texto libre, max_length=256
    "cbte_id_condicion_vta",  # id_afip, tiene que estar cargado
    "cbte_condicion_vta_otra",  # texto libre, solo si condicion_vta es otra
    # ----detalle
    "det_codigo",  # codigo de producto, opcional max_length=128
    "det_nombre",  # obligatorio si no existe el cod producto, sino se toma del producto max_length=256
    "det_cant",  # obligatorio, decimal
    "det_precio_unit",  # obligatorio si no existe el cod producto, sino se toma del producto
    "det_unidad",  # id_afip, tiene que estar cargado, obligatorio si no existe el cod producto
    "det_id_alicuota",  # id_afip, tiene que estar cargado, obligatorio si no existe el cod producto
    # ----tributos
    "trib_id",  # id_afip, tiene que estar cargado,
    "trib_detalle",  # texto libre, max_length=256
    "trib_base_imponible",  # obligatorio, decimal
    "trib_alicuota",  # obligatorio, decimal
    # ----opcionales
    "op_id",  # id_afip, tiene que estar cargado,
    "op_valor",  # max_length=256
]


def get_or_error(errors, linen, record, field_name, obj_list, verbose_name, opcional=False, default=None):
    ret = None
    try:
        val = record.get(field_name, default) or default
        if not val:
            if opcional:
                return None
            errors.append("La columna '{}' en la linea nro {} no puede estar vacia".format(verbose_name, linen))
        else:
            if str(val) in obj_list:
                ret = obj_list[str(val)]
            else:
                errors.append(
                    "La columna '{}' en la linea nro {} tiene un valor incorrecto. "
                    "Los valores posibles son: {}".format(verbose_name, linen,
                                                          ", ".join(list(obj_list.keys()))))
    except:
        errors.append("Error al procesar la columna {} de la linea {}".format(verbose_name, linen))

    return ret

def get_nro_dni_or_error(errors, linen, record, field_name, verbose_name, opcional=False, default=None):
    ret = None
    try:
        val = record.get(field_name, default) or default
        if not val:
            if opcional:
                return None
            errors.append("La columna '{}' en la linea nro {} no puede estar vacia".format(verbose_name, linen))
        else:
            if str(val):
                ret = str(val)
            else:
                errors.append(
                    "La columna '{}' en la linea nro {} tiene un valor incorrecto. "
                    "Los valores posibles son: {}".format(verbose_name, linen,
                                                          ", ".join(list(obj_list.keys()))))
    except:
        errors.append("Error al procesar la columna {} de la linea {}".format(verbose_name, linen))

    return ret


def check_str(errors, linen, record, field_name, max_length, verbose_name):
    val = record.get(field_name, "")
    try:
        if len(val) > max_length:
            errors.append(
                "La longitud del valor de la columna '{}' en la linea nro {} debe ser menor a {}".format(verbose_name,
                                                                                                         linen, max_length))
            val = ""
    except:
        errors.append("Error al procesar la columna {} de la linea {}".format(verbose_name, linen))

    return val


def check_date(errors, linen, record, field_name, verbose_name):
    val = record.get(field_name, "")
    ret = None
    try:
        ret = datetime.datetime.strptime(val, '%d/%m/%Y').date()
    except:
        errors.append(
            "El formato de fecha de la columna '{}' en la linea nro {} debe ser 'DD/MM/AAAA".format(verbose_name,
                                                                                                    linen))
    return ret


def check_float(errors, linen, record, field_name, verbose_name, default=None):
    val = record.get(field_name, default) or default
    ret = None
    try:
        if not default:
            ret = float(val.replace(',','.'))
        else:
            ret = float(val)
    except:
        errors.append("El valor de la columna '{}' en la linea nro {} debe ser un decimal".format(verbose_name, linen))
    return ret


classes_to_prefetch = ((TipoComprobante, "id_afip"),
                       (Concepto, "id_afip"),
                       (TipoDoc, "id_afip"),
                       (TipoExportacion, "id_afip"),
                       (Moneda, "id_afip"),
                       (Idioma, "id_afip"),
                       (Incoterms, "id_afip"),
                       (PaisDestino, "id_afip"),
                       (CondicionVenta, "id"),
                       (Unidad, "id_afip"),
                       (AlicuotaIva, "id_afip"),
                       (CondicionIva, "id_afip"),
                       (PuntoDeVenta, "id_afip"),
                       (Producto, "codigo"),
                       (Tributo, "id_afip"),
                       (Opcional, "id_afip"))


def _prefetch(empresa):
    ret = {}
    for cls, field in classes_to_prefetch:
        ret[cls] = {str(getattr(i, field)): i for i in cls.objects.all()}
    ret[Cliente] = {(c.tipo_doc.id_afip, c.nro_doc): c for c in Cliente.objects.all()}
    ret[Opcional] = {o.id_afip: o for o in empresa.get_opcionales()}
    return ret

def cliente_changed(cliente, nombre, condicion_iva, domicilio, localidad, telefono, cod_postal, email):
    return cliente.nombre != nombre or cliente.condicion_iva != condicion_iva or cliente.domicilio != domicilio or cliente.localidad != localidad or cliente.telefono != telefono or cliente.cod_postal != cod_postal or cliente.email != email


def import_cbte_csv(csvfile):
    errors = []
    lineerrs = []
    linen = 0
    empresa = Empresa.objects.first()
    prefetched = _prefetch(empresa)
    try:
        with transaction.atomic():
            records = csv.DictReader(csvfile, fieldnames=cbte_import_fields, restval=None)
            last_item_number = None
            last_cbte = None

            for record in records:
                linen += 1
                lineerrs = []
                if not record["cbte_item_number"]:
                    lineerrs.append("la linea {} del archivo no tiene un numero de item".format(linen))
                    continue
                if record["cbte_item_number"] != last_item_number:
                    last_cbte = None
                    last_item_number = record["cbte_item_number"]
                    # creo cbte
                    tipo_cbte = get_or_error(lineerrs, linen, record, "cbte_tipo_cbte", prefetched[TipoComprobante],
                                             "tipo de comprobante")
                    punto_vta = get_or_error(lineerrs, linen, record, "cbte_punto_vta", prefetched[PuntoDeVenta],
                                             "punto de venta")
                    concepto = get_or_error(lineerrs, linen, record, "cbte_concepto", prefetched[Concepto], "concepto")
                    nro_remito = check_str(lineerrs, linen, record, "cbte_nro_remito", 13, "numero de remito")
                    fecha_emision = check_date(lineerrs, linen, record, "cbte_fecha_emision", "fecha de emision")
                    fecha_vto = check_date(lineerrs, linen, record, "cbte_fecha_vencimiento",
                                           "fecha de vencimiento de pago")
                    tipo_doc = get_or_error(lineerrs, linen, record, "cbte_id_tipo_doc_cliente", prefetched[TipoDoc],
                                            "tipo de documento del cliente")
                    nro_doc = check_str(lineerrs, linen, record, "cbte_nro_doc_cliente", 128,
                                        "numero de documento del cliente")

                    tipo_expo = get_or_error(lineerrs, linen, record, "cbte_tipo_exportacion",
                                             prefetched[TipoExportacion],
                                             "tipo de exportacion", opcional=True)

                    moneda = get_or_error(lineerrs, linen, record, "cbte_id_moneda", prefetched[Moneda],
                                          "moneda", default="PES")

                    cotizaccion = check_float(lineerrs, linen, record, "cbte_moneda_ctz", "cotizacion", default=1)
                    idioma = get_or_error(lineerrs, linen, record, "cbte_id_idioma", prefetched[Idioma],
                                          "idioma", default=1)
                    incoterms = get_or_error(lineerrs, linen, record, "cbte_id_incoterms", prefetched[Incoterms],
                                             "incoterms", opcional=True)
                    incoterms_ds = check_str(lineerrs, linen, record, "cbte_incoterms_ds", 256,
                                             "incoterms - descripcion")
                    pais_destino = get_or_error(lineerrs, linen, record, "cbte_id_pais_destino",
                                                prefetched[PaisDestino],
                                                "pais de destino", opcional=True)

                    id_impositivo = check_str(lineerrs, linen, record, "cbte_id_impositivo", 256,
                                              "id impositivo")

                    obs_comerciales = check_str(lineerrs, linen, record, "cbte_observaciones_comerciales", 9999,
                                                "observaciones comerciales")
                    obs = check_str(lineerrs, linen, record, "cbte_observaciones", 9999,
                                    "observaciones")
                    forma_pago = check_str(lineerrs, linen, record, "cbte_forma_pago", 256,
                                           "forma de pago")
                    condicion_vta = get_or_error(lineerrs, linen, record, "cbte_id_condicion_vta",
                                                 prefetched[CondicionVenta],
                                                 "condicion de venta")
                    condicion_vta_texto = check_str(lineerrs, linen, record, "cbte_condicion_vta_otra", 256,
                                                    "condicion de venta - otra")

                    # Info cliente
                    nombre = check_str(lineerrs, linen, record, "cbte_cliente_nombre", 256,
                                           "razon social del cliente")
                    condicion_iva = get_or_error(lineerrs, linen, record, "cbte_cliente_condicion_iva",
                                                 prefetched[CondicionIva],
                                                 "condicion de iva del cliente")
                    domicilio = check_str(lineerrs, linen, record, "cbte_cliente_domicilio", 256,
                                          "domicilio del cliente")
                    localidad = check_str(lineerrs, linen, record, "cbte_cliente_localidad", 256,
                                          "localidad del cliente")
                    telefono = check_str(lineerrs, linen, record, "cbte_cliente_telefono", 256,
                                         "telefono del cliente")
                    cod_postal = check_str(lineerrs, linen, record, "cbte_cliente_cp", 256,
                                           "codigo postal del cliente")
                    email = check_str(lineerrs, linen, record, "cbte_cliente_email", 75,
                                      "email del cliente")

                    if (tipo_doc.id_afip, nro_doc) in prefetched[Cliente]:
                        cliente = prefetched[Cliente][(tipo_doc.id_afip, nro_doc)]
                        if cliente_changed(cliente, nombre, condicion_iva, domicilio, localidad, telefono, cod_postal, email):
                            cliente.nombre = nombre
                            cliente.condicion_iva = condicion_iva
                            cliente.domicilio = domicilio
                            cliente.localidad = localidad
                            cliente.telefono = telefono
                            cliente.cod_postal = cod_postal
                            cliente.email = email
                            cliente.save()
                    else:
                        cliente = Cliente(tipo_doc=tipo_doc, nro_doc=nro_doc, nombre=nombre,
                                          condicion_iva=condicion_iva, domicilio=domicilio,
                                          localidad=localidad, telefono=telefono, cod_postal=cod_postal, email=email)
                        cliente.save()
                        prefetched[Cliente][(tipo_doc.id_afip, nro_doc)] = cliente

                    last_cbte = Comprobante(
                        empresa=empresa,
                        tipo_cbte=tipo_cbte,
                        punto_vta=punto_vta,
                        concepto=concepto,
                        remito_nro=nro_remito,
                        fecha_emision=fecha_emision,
                        fecha_venc_pago=fecha_vto,
                        cliente_id=cliente.id,
                        tipo_expo=tipo_expo,
                        moneda=moneda,
                        idioma=idioma,
                        incoterms=incoterms,
                        pais_destino=pais_destino,
                        id_impositivo=id_impositivo,
                        moneda_ctz=Decimal(cotizaccion),
                        observaciones_comerciales=obs_comerciales,
                        observaciones=obs,
                        forma_pago=forma_pago,
                        incoterms_ds=incoterms_ds,
                        condicion_venta=condicion_vta,
                        condicion_venta_texto=condicion_vta_texto,
                    )
                    last_cbte.save()


                if record["det_nombre"] or record["det_codigo"]:
                    codigo = check_str(lineerrs, linen, record, "det_codigo", 128, "codigo de producto")
                    cantidad = check_float(lineerrs, linen, record, "det_cant", "cantidad")

                    if codigo:
                        if codigo in prefetched[Producto]:
                            prod = prefetched[Producto][codigo]
                        else:
                            nombre = check_str(lineerrs, linen, record, "det_nombre", 256, "texto del detalle")
                            precio_unit = check_float(lineerrs, linen, record, "det_precio_unit", "precio unitario")
                            unidad = get_or_error(lineerrs, linen, record, "det_unidad", prefetched[Unidad],
                                                  "unidad de medida")
                            alicuota = get_or_error(lineerrs, linen, record, "det_id_alicuota", prefetched[AlicuotaIva],
                                                    "alicuota IVA")
                            prod = Producto(
                                codigo=codigo,
                                nombre=nombre,
                                precio_unit=Decimal(precio_unit),
                                alicuota_iva=alicuota,
                                unidad=unidad
                            )
                            prefetched[Producto][codigo] = prod
                            prod.save()
                        det = DetalleComprobante(
                            comprobante_id=last_cbte.id,
                            producto_id=prod.id,
                            cant=Decimal(cantidad),
                            detalle=prod.nombre_completo,
                            precio_unit=prod.precio_unit,
                            alicuota_iva=prod.alicuota_iva,
                            unidad=prod.unidad
                        )
                    else:
                        nombre = check_str(lineerrs, linen, record, "det_nombre", 256, "texto del detalle")
                        precio_unit = check_float(lineerrs, linen, record, "det_precio_unit", "precio unitario")
                        unidad = get_or_error(lineerrs, linen, record, "det_unidad", prefetched[Unidad],
                                              "unidad de medida")
                        alicuota = get_or_error(lineerrs, linen, record, "det_id_alicuota", prefetched[AlicuotaIva],
                                                "alicuota IVA")
                        det = DetalleComprobante(
                            comprobante_id=last_cbte.id,
                            cant=Decimal(cantidad),
                            detalle=nombre,
                            precio_unit=Decimal(precio_unit),
                            alicuota_iva=alicuota,
                            unidad=unidad
                        )

                    det.save()

                if record["trib_id"]:
                    tributo = get_or_error(lineerrs, linen, record, "trib_id", prefetched[Tributo],
                                           "tributo")
                    detalle = check_str(lineerrs, linen, record, "trib_detalle", 256, "detalle del tributo")
                    base_imponible = check_float(lineerrs, linen, record, "trib_base_imponible", "base imponible")
                    alicuota = check_float(lineerrs, linen, record, "trib_alicuota", "alicuota")

                    trib = TributoComprobante(
                        comprobante_id=last_cbte.id,
                        tributo_id=tributo.id,
                        detalle=detalle,
                        base_imponible=Decimal(base_imponible),
                        alicuota=Decimal(alicuota)
                    )
                    trib.save()
                if record["op_id"]:
                    opcional = get_or_error(lineerrs, linen, record, "op_id", prefetched[Opcional],
                                            "opcional")
                    valor = check_str(lineerrs, linen, record, "op_valor", 256, "valor del opcional")

                    op = OpcionalComprobante(
                        comprobante_id=last_cbte.id,
                        opcional_id=opcional.id,
                        valor=valor
                    )
                    op.save()

                errors.extend(lineerrs)
                lineerrs = []
        if errors:
            raise Exception()

    except Exception as e:
        errors.extend(lineerrs)
        errors.append("Hubo un error al procesar el archivo. Ultima linea procesada: {}".format(linen or 0))
        logger.exception("Error al importar")

    return errors


def import_product_csv(csvfile, update_existing, exclude_first_line, is_final_price):
    errors = []
    ignored = 0
    imported = 0
    updated = 0
    linen = 0
    lineerrs = []
    empresa = Empresa.objects.first()
    prefetched = _prefetch(empresa)
    try:
        with transaction.atomic():
            records = csv.DictReader(csvfile, fieldnames=prod_import_fields, restval=None)
            if exclude_first_line:
                records = iter(records)
                next(records)

            for record in records:
                linen += 1
                lineerrs = []
                prod = None

                # chequeo si el producto existe
                codigo = check_str(lineerrs, linen, record, "prod_codigo", 128, "codigo de producto")
                codigo_barras = check_str(lineerrs, linen, record, "prod_codigo_barras", 128, "codigo de barras de producto")
                codigo_barras = codigo_barras if codigo_barras else None
                if codigo and codigo in prefetched[Producto]:
                    prod = prefetched[Producto][codigo]

                nombre = check_str(lineerrs, linen, record, "prod_nombre", 256, "nombre del producto")
                precio_unit = check_float(lineerrs, linen, record, "prod_precio_unit", "precio unitario")
                unidad = get_or_error(lineerrs, linen, record, "prod_unidad", prefetched[Unidad],
                                      "unidad de medida", opcional=True)
                alicuota = get_or_error(lineerrs, linen, record, "prod_alicuota_iva", prefetched[AlicuotaIva],
                                        "alicuota IVA", opcional=True)

                if not alicuota:
                    #default 21%
                    alicuota = prefetched[AlicuotaIva][str(AlicuotaIva.IVA_21)]
                elif is_final_price and alicuota.porc > 0:
                    precio_unit = Decimal(precio_unit)/(1+alicuota.porc/100)

                if not unidad:
                    #default unidades
                    unidad = prefetched[Unidad][str(Unidad.UNIDADES_ID_AFIP)]

                if prod:
                    if update_existing:
                        #actualizo
                        prod.nombre = nombre
                        prod.precio_unit = Decimal(precio_unit)
                        prod.alicuota_iva = alicuota
                        prod.unidad = unidad
                        prod.codigo_barras_nro = codigo_barras
                        prod.ingresa_precio_final = is_final_price
                        prod.alta_edi = False
                        prod.activo = True

                        if lineerrs:
                            raise Exception()

                        updated += 1
                        prod.save()
                    else:
                        ignored += 1
                else:
                    #creo prod desde cero
                    prod = Producto(
                        codigo=codigo,
                        nombre=nombre,
                        precio_unit=Decimal(precio_unit),
                        alicuota_iva=alicuota,
                        unidad=unidad,
                        codigo_barras_nro=codigo_barras,
                        ingresa_precio_final=is_final_price,
                        alta_edi=False
                    )

                    if lineerrs:
                        raise Exception()

                    imported += 1
                    prod.save()

                errors.extend(lineerrs)
                lineerrs = []
        if errors:
            raise Exception()

    except Exception as e:
        errors.extend(lineerrs)
        errors.append("Hubo un error al procesar el archivo. Ultima linea procesada: {}".format(linen or 0))
        logger.exception("Error al importar")

    return errors, imported, ignored, updated


def import_client_csv(csvfile, update_existing, exclude_first_line):
    errors = []
    ignored = 0
    imported = 0
    updated = 0
    linen = 0
    lineerrs = []
    ultimo_codigo = 0
    empresa = Empresa.objects.first()
    prefetched = _prefetch(empresa)
    try:
        with transaction.atomic():
            records = csv.DictReader(csvfile, fieldnames=cli_import_fields, restval=None)
            last_item_number = None
            if exclude_first_line:
                records = iter(records)
                next(records)

            for record in records:
                linen += 1
                lineerrs = []
                if not record["cli_item_number"]:
                    lineerrs.append("la linea {} del archivo no tiene un numero de item".format(linen))
                    continue
                if record["cli_item_number"] != last_item_number:
                    last_item_number = record["cli_item_number"]

                    # chequeo si el cliente existe
                    tipo_doc = get_or_error(lineerrs, linen, record, "cli_tipo_doc", prefetched[TipoDoc],
                                          "Tipo de Documento", opcional=True)
                    nro_doc = get_nro_dni_or_error(lineerrs, linen, record, "cli_nro_doc", "numero de documento")

                    cli = None
                    if tipo_doc and nro_doc:
                        cli = dict((k, v) for k, v in prefetched[Cliente].items()
                                   if (k[0], k[1].strip()) == (tipo_doc.id_afip, nro_doc) and v.editable)
                        cli = next(iter(cli.values())) if list(cli.values()) else None
                    else:
                        #default OTRO
                        tipo_doc = prefetched[TipoDoc][str(TipoDoc.OTRO)]

                    nombre = check_str(lineerrs, linen, record, "cli_nombre", 256, "nombre del cliente")
                    domicilio = check_str(lineerrs, linen, record, "cli_domicilio", 256, "domicilio del cliente")
                    localidad = check_str(lineerrs, linen, record, "cli_localidad", 256, "localidad del cliente")
                    telefono = check_str(lineerrs, linen, record, "cli_telefono", 256, "telefono del cliente")
                    cod_postal = check_str(lineerrs, linen, record, "cli_cod_postal", 256, "codigo postal del cliente")
                    email = check_str(lineerrs, linen, record, "cli_email", 256, "email del cliente")
                    condicion_iva = get_or_error(lineerrs, linen, record, "cli_condicion_iva", prefetched[CondicionIva],
                                          "Condicion de IVA", opcional=True)

                    if not condicion_iva:
                        #default consumidor final
                        condicion_iva = prefetched[CondicionIva][str(CondicionIva.CONS_FINAL)]

                    if cli:
                        if update_existing:
                            #actualizo
                            cli.nombre = nombre
                            cli.condicion_iva = condicion_iva
                            cli.domicilio = domicilio
                            cli.localidad = localidad
                            cli.telefono = telefono
                            cli.cod_postal = cod_postal
                            cli.email = email
                            cli.activo = True

                            if lineerrs:
                                raise Exception()

                            updated += 1
                            cli.save()
                        else:
                            ignored += 1
                    else:
                        #creo cliente desde cero
                        if ultimo_codigo == 0:
                            cli_list = prefetched[Cliente]
                            cli_list = iter(cli_list.values())
                            cli_list = sorted(cli_list, key=lambda x: x.id)
                            ultimo_codigo = cli_list[-1].id if cli_list else 0

                        ultimo_codigo = int(ultimo_codigo)+1 if ultimo_codigo > 0 and ultimo_codigo != "" else 1

                        cli = Cliente(
                            nombre=nombre,
                            tipo_doc=tipo_doc,
                            nro_doc=nro_doc,
                            condicion_iva=condicion_iva,
                            domicilio=domicilio,
                            localidad=localidad,
                            telefono=telefono,
                            cod_postal=cod_postal,
                            email=email,
                            activo=True,
                        )

                        if lineerrs:
                            raise Exception()

                        imported += 1
                        cli.save()

                errors.extend(lineerrs)
                lineerrs = []
        if errors:
            raise Exception()

    except Exception as e:
        errors.extend(lineerrs)
        errors.append("Hubo un error al procesar el archivo. Ultima linea procesada: {}".format(linen or 0))
        logger.exception("Error al importar")

    return errors, imported, ignored, updated