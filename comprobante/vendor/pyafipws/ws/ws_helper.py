# coding=utf-8
import json
import re
from afip.models import AlicuotaIva, TipoComprobante, Concepto
from comprobante.models import Comprobante
from comprobante.vendor.pyafipws.ws.utils import date
from main.redis import get_redis_client

__author__ = 'mlambir'

import tempfile
from . import wsaa
from . import wsfev1
from . import wsfexv1
from .soap import SimpleXMLElement
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

cert2 = os.path.abspath("res/afip_ca_info.crt")


def auth(cert, key, service):
    r = get_redis_client()
    data = r.get("pirra-auth-{}".format(service))
    if data:
        data = json.loads(data)
        return data["token"], data["sign"], SimpleXMLElement(data["ta"])
    else:

        # self.log("Creando TRA...")
        tra = wsaa.create_tra(service=service)
        # self.log("Frimando TRA (CMS)...")
        cms = wsaa.sign_tra(str(tra), cert, key)
        # self.log("Llamando a WSAA...")
        xml = wsaa.call_wsaa(str(cms), settings.WSAA_URL)
        # self.log("Procesando respuesta...")
        ta = SimpleXMLElement(xml)

        r.set("pirra-auth-{}".format(service),json.dumps({
            "token": str(ta.credentials.token),
            "sign": str(ta.credentials.sign),
            "ta": ta.asXML()
        }))
        r.expireat("pirra-auth-{}".format(service), date('U')+23000)

    return ta.credentials.token, ta.credentials.sign, ta


_f = "{0:.2f}".format


def setupWSFE(cuit, cert, key):
    token, sign, ta = auth(cert.name, key.name, "wsfe")
    wsfe = wsfev1.WSFEv1()
    wsfe.Token = token
    wsfe.Sign = sign
    wsfe.Cuit = cuit

    wsfe.SetTicketAcceso(ta.asXML())

    # Conectar al Servicio Web de Facturación
    cache = proxy = ""
    wrapper = ""

    cacert = None  # No validamos mas el cacert, le dejamos la validacion a la libreria
    ok = wsfe.Conectar(cache, settings.WSFE_URL, proxy, wrapper, cacert)

    if not ok:
        raise RuntimeError(wsfe.Excepcion)
    return wsfe


def setupWSFEX(cuit, cert, key):
    token, sign, ta = auth(cert.name, key.name, "wsfex")
    wsfex = wsfexv1.WSFEXv1()
    wsfex.Token = token
    wsfex.Sign = sign
    wsfex.Cuit = cuit

    wsfex.SetTicketAcceso(ta.asXML())

    # Conectar al Servicio Web de Facturación
    cache = proxy = ""
    wrapper = "httplib2"
    cacert = None  # No validamos mas el cacert, le dejamos la validacion a la libreria
    ok = wsfex.Conectar(cache, settings.WSFEX_URL, proxy, wrapper, cacert)

    if not ok:
        raise RuntimeError(wsfex.Excepcion)
    return wsfex


def eliminar_nro_comprobantes_existentes(cbte_nro, punto_vta, tipo_cbte):
    # busco si hay cbtes con mismo (num, tipo_cbte, pto_vta) y les nulleo el numero
    Comprobante.objects.filter(nro=cbte_nro, punto_vta__id_afip=punto_vta, tipo_cbte__id_afip=tipo_cbte).update(nro=None)


def autorizar_cbte(cbte, punto_vta, tipo_cbte, wsfe):
    # si no me especifícan nro de comprobante, busco el próximo
    cbte_nro = wsfe.CompUltimoAutorizado(tipo_cbte, punto_vta)
    cbte_nro = int(cbte_nro or "0") + 1

    eliminar_nro_comprobantes_existentes(cbte_nro, punto_vta, tipo_cbte)

    cbte.nro = cbte_nro
    cbte.save()

    # genero alicuotas iva:
    alicuotas = {}
    if tipo_cbte not in (
    TipoComprobante.FACTURA_C, TipoComprobante.ND_C, TipoComprobante.NC_C, TipoComprobante.RECIBO_C):
        for detalle in cbte.detallecomprobante_set.all():
            key = detalle.alicuota_iva.id_afip
            if key in alicuotas:
                alicuotas[key]["importe_neto"] += detalle.importe_neto
                alicuotas[key]["importe_iva"] += detalle.importe_iva
            else:
                alicuotas[key] = {
                    "importe_neto": detalle.importe_neto,
                    "importe_iva": detalle.importe_iva
                }
    fecha = cbte.fecha_emision.strftime("%Y%m%d")
    tipo_doc = cbte.cliente.tipo_doc.id_afip
    nro_doc = re.sub(r'\W+', '', str(cbte.cliente.nro_doc))
    cbt_desde = cbte_nro
    cbt_hasta = cbt_desde
    imp_total = _f(cbte.importe_total)
    imp_tot_conc = _f(cbte.importe_no_gravado)
    imp_neto = _f(cbte.importe_neto_gravado)
    imp_trib = _f(cbte.importe_tributos)
    imp_op_ex = _f(cbte.importe_exento)
    imp_iva = _f(cbte.importe_iva)
    fecha_cbte = fecha
    # Fechas del período del servicio facturado
    concepto = cbte.concepto.id_afip
    if concepto == Concepto.PRODUCTOS:
        fecha_venc_pago = fecha_serv_desde = fecha_serv_hasta = None
    else:
        fecha_venc_pago = cbte.fecha_venc_pago.strftime("%Y%m%d")
        fecha_serv_desde = fecha
        fecha_serv_hasta = fecha
    moneda_id = cbte.moneda.id_afip
    moneda_ctz = cbte.moneda_ctz
    wsfe.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                      cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
                      imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago,
                      fecha_serv_desde, fecha_serv_hasta,  # --
                      moneda_id, moneda_ctz)
    # agrego alicuotas iva
    if len(alicuotas):
        for alicuota_id_afip, importes in list(alicuotas.items()):
            if alicuota_id_afip not in (AlicuotaIva.EXENTO, AlicuotaIva.NO_GRAVADO):
                wsfe.AgregarIva(alicuota_id_afip, _f(importes["importe_neto"]), _f(importes["importe_iva"]))

                # agrego un comprobante asociado (solo notas de crédito / débito)
                # if tipo_cbte in (2, 3, 7, 8): # TODO para asociar comprobantes
                # tipo = 1
                # pv = 2
                # nro = 1234
                # wsfe.AgregarCmpAsoc(tipo, pv, nro)

    # agrego otros tributos
    for tributo in cbte.tributocomprobante_set.all():
        wsfe.AgregarTributo(tributo.tributo.id_afip, tributo.detalle, _f(tributo.base_imponible), _f(tributo.alicuota),
                            _f(tributo.total))

    # agrego opcionales
    actividad_comprendida = False
    for opcional in cbte.opcionalcomprobante_set.order_by('opcional__id_afip').all():
        if opcional.opcional.id_afip == '10' and opcional.valor == '1':
            actividad_comprendida = True

        if opcional.opcional.id_afip in ['1011', '1012'] and not actividad_comprendida:
            continue

        wsfe.AgregarOpcional(opcional.opcional.id_afip, opcional.valor)

    # llamo al websevice para obtener el CAE:
    wsfe.CAESolicitar()

    # me aseguro de que si falló la autorización, el comprobante quede sin numero
    if not len(wsfe.CAE):
        cbte.nro = None
        cbte.save()
    return wsfe


def autorizarWSFE(cbte, cert, key, cbte_nro=None):
    wsfe = setupWSFE(int(cbte.empresa.nro_doc), cert, key)

    punto_vta = cbte.punto_vta.id_afip
    tipo_cbte = cbte.tipo_cbte.id_afip

    # Si tiene numero, consulto si ya está autorizado
    if cbte.nro:
        wsfe.CompConsultar(tipo_cbte, punto_vta, cbte.nro)

    if len(wsfe.CAE):
        # Si está autorizado, el CAE del comprobante debe ser único en el sistema (por tipo_cbte y punto_vta)
        cae_existente = Comprobante.objects.filter(tipo_cbte__id_afip=tipo_cbte, punto_vta__id_afip=punto_vta, cae=wsfe.CAE)
        if len(cae_existente):
            # Existe otro con mismo numero, pto_vta y tipo_comp autorizado. El numero asignado previamente ya no sirve.
            cbte.nro = None
            wsfe = autorizar_cbte(cbte, punto_vta, tipo_cbte, wsfe)
    else:
        # No está autorizado, mando a autorizar.
        wsfe = autorizar_cbte(cbte, punto_vta, tipo_cbte, wsfe)
    return wsfe


def autorizar(cbte, certificate, private_key):
    empresa = cbte.empresa

    cert, key = get_cert_and_key(certificate, private_key)

    if cbte.tipo_cbte.id_afip in (TipoComprobante.FACTURA_A, TipoComprobante.ND_A, TipoComprobante.NC_A, TipoComprobante.RECIBO_A,
                                  TipoComprobante.FACTURA_B, TipoComprobante.ND_B, TipoComprobante.NC_B, TipoComprobante.RECIBO_B,
                                  TipoComprobante.FACTURA_C, TipoComprobante.ND_C, TipoComprobante.NC_C, TipoComprobante.RECIBO_C,
                                  TipoComprobante.FACTURA_M, TipoComprobante.NC_M, TipoComprobante.ND_M, TipoComprobante.RECIBO_M):

        return autorizarWSFE(cbte, cert, key, cbte.nro)

    elif cbte.tipo_cbte.id_afip in (TipoComprobante.FACTURA_E, TipoComprobante.ND_E, TipoComprobante.NC_E):
        wsfex = setupWSFEX(int(empresa.nro_doc), cert, key)

        if not cbte.id_lote_afip:
            last_id = wsfex.GetLastID()
            if not last_id:
                last_id = 0
                logger.error([e for e in wsfex.Errores])
                logger.error([e for e in wsfex.Observaciones])
            cbte.id_lote_afip = int(last_id) + 1
            cbte.save()

        last_cmp = wsfex.GetLastCMP(cbte.tipo_cbte.id_afip, cbte.punto_vta.id_afip)
        if not last_cmp:
            last_cmp = 0
            logger.error([e for e in wsfex.Errores])
            logger.error([e for e in wsfex.Observaciones])
        cbte_nro = int(last_cmp) + 1
        cbte.nro = cbte_nro

        eliminar_nro_comprobantes_existentes(cbte_nro, cbte.punto_vta.id_afip, cbte.tipo_cbte.id_afip)

        tipo_expo = cbte.tipo_expo.id_afip
        permiso_existente = "" if (cbte.tipo_cbte.id_afip in (TipoComprobante.ND_E, TipoComprobante.NC_E) or tipo_expo in (2, 4)) else "S"
        dst_cmp = cbte.pais_destino.id_afip
        cuit_pais_cliente = cbte.pais_destino.cuit
        id_impositivo = cbte.id_impositivo
        moneda_id = cbte.moneda.id_afip
        moneda_ctz = cbte.moneda_ctz
        obs_comerciales = cbte.observaciones_comerciales
        obs = cbte.observaciones
        forma_pago = cbte.forma_pago
        incoterms = cbte.incoterms.id_afip if cbte.incoterms else None
        incoterms_ds = cbte.incoterms_ds
        idioma_cbte = cbte.idioma.id_afip
        fecha_pago = cbte.fecha_pago.strftime("%Y%m%d") if cbte.fecha_pago else ''
        
        # Creo una factura (internamente, no se llama al WebService):
        ok = wsfex.CrearFactura(cbte.tipo_cbte.id_afip, cbte.punto_vta.id_afip, cbte_nro,
                                cbte.fecha_emision.strftime("%Y%m%d"),
                                _f(cbte.importe_total), tipo_expo, permiso_existente, dst_cmp,
                                cbte.cliente.nombre, cuit_pais_cliente, cbte.cliente.domicilio,
                                id_impositivo, moneda_id, moneda_ctz,
                                obs_comerciales, obs, forma_pago, incoterms,
                                idioma_cbte, incoterms_ds, fecha_pago)

        for detalle in cbte.detallecomprobante_set.all():
            # Agrego un item:
            codigo = detalle.pk
            ds = detalle.detalle
            qty = detalle.cant
            precio = _f(detalle.precio_unit)
            umed = detalle.unidad.id_afip
            bonif = "0.00"
            imp_total = _f(detalle.precio_total)
            ok = wsfex.AgregarItem(codigo, ds, qty, umed, precio, imp_total, bonif)

        # informo un comprobante asociado (solo notas de credito / debito de exportacion)
        if cbte.cbte_asoc:
            tipo_cbte = cbte.cbte_asoc.tipo_cbte.id_afip
            pto_venta = cbte.cbte_asoc.punto_vta.id_afip
            nro = cbte.cbte_asoc.nro
            wsfex.AgregarCmpAsoc(tipo_cbte, pto_venta, nro)

        # Llamo al WebService de Autorización para obtener el CAE
        cae = wsfex.Authorize(cbte.id_lote_afip)

        if not cae:
            cbte.nro = None
            if wsfex.Errores:
                logger.error([e for e in wsfex.Errores])
                logger.error([e for e in wsfex.Observaciones])
                # adapto Errores para que tenga el mismo manejo que con WSFEv1
                wsfex.Errores = [str(error.encode("utf-8").decode("latin1")) for error in wsfex.Errores]
        if wsfex.Vencimiento:
            wsfex.Vencimiento = "%s/%s/%s" % (wsfex.Vencimiento[6:10], wsfex.Vencimiento[3:5], wsfex.Vencimiento[0:2])
            wsfex.Vencimiento = wsfex.Vencimiento.replace("/", "")
        return wsfex


def get_cert_and_key(certificate, private_key):
    cert = tempfile.NamedTemporaryFile()
    key = tempfile.NamedTemporaryFile()

    cert.write(certificate)
    key.write(private_key)

    key.flush()
    cert.flush()
    return cert, key


def check_status(cuit, certificate, private_key):
    cert, key = get_cert_and_key(certificate, private_key)

    wsfe = setupWSFE(cuit, cert, key)
    wsfe.Dummy()

    ret = dict(AppServerStatus=wsfe.AppServerStatus.lower(), DbServerStatus=wsfe.DbServerStatus.lower(), AuthServerStatus=wsfe.AuthServerStatus.lower())
    return ret


def consultar_comprobante(certificate, private_key, cuit, tipo_cbte, punto_vta, nro):
    if not tipo_cbte or not punto_vta or not nro:
        raise Exception("Debe ingresar tipo cbte, punto de venta y numero.")

    cert, key = get_cert_and_key(certificate, private_key)

    wsfe = setupWSFE(cuit, cert, key)

    wsfe.CompConsultar(tipo_cbte, punto_vta, nro)

    return wsfe