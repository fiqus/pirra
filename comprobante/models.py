import datetime
from decimal import Decimal

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.core.files.storage import FileSystemStorage

# Create your models here.
from afip.models import TipoComprobante, AlicuotaIva, TipoExportacion, Moneda, Idioma, Incoterms, \
    PaisDestino, Unidad, CondicionVenta, Concepto, Tributo, Opcional
from empresa.models import Empresa, PuntoDeVenta, Cliente, BajaLogicaClass

fs = FileSystemStorage(location='/media/codigos_barras')


def venc_default():
    return datetime.date.today() + datetime.timedelta(days=30)  # por ahora vence en 30 dias


class Comprobante(models.Model):
    id_lote_afip = models.IntegerField(null=True)

    empresa = models.ForeignKey(Empresa, default=1, on_delete=models.CASCADE)

    tipo_cbte = models.ForeignKey(TipoComprobante, default=1, on_delete=models.CASCADE)
    punto_vta = models.ForeignKey(PuntoDeVenta, default=1, on_delete=models.CASCADE)
    concepto = models.ForeignKey(Concepto, on_delete=models.CASCADE)

    nro = models.IntegerField(null=True)
    remito_nro = models.CharField(max_length=13, blank=True, default='', null=True)
    fecha_emision = models.DateField(default=datetime.date.today)
    fecha_venc_pago = models.DateField(default=venc_default)

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    cae = models.CharField(max_length=256, blank=True)
    fecha_vto_cae = models.DateField(blank=True, null=True)
    resultado = models.CharField(max_length=256, blank=True)
    motivo = models.CharField(max_length=256, blank=True, null=True)
    reproceso = models.CharField(max_length=256, blank=True)
    codigo_barras = models.ImageField(null=True, blank=True, upload_to="codigos_barras")
    codigo_barras_nro = models.CharField(max_length=256, blank=True)

    tipo_expo = models.ForeignKey(TipoExportacion, null=True, blank=True, on_delete=models.CASCADE)
    moneda = models.ForeignKey(Moneda, null=True, blank=True, on_delete=models.CASCADE)
    idioma = models.ForeignKey(Idioma, null=True, blank=True, on_delete=models.CASCADE)
    incoterms = models.ForeignKey(Incoterms, null=True, blank=True, on_delete=models.CASCADE)
    pais_destino = models.ForeignKey(PaisDestino, null=True, blank=True, on_delete=models.CASCADE)

    id_impositivo = models.CharField(max_length=256, blank=True, null=True)
    moneda_ctz = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)
    observaciones_comerciales = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    errores_wsfe = models.TextField(blank=True, null=True)
    observaciones_wsfe = models.TextField(blank=True, null=True)

    forma_pago = models.CharField(max_length=256, blank=True, null=True)
    incoterms_ds = models.CharField(max_length=256, blank=True, null=True)
    condicion_venta = models.ForeignKey(CondicionVenta, null=True, blank=True, on_delete=models.CASCADE)
    condicion_venta_texto = models.CharField(max_length=256, blank=True, null=True)
    # Porcentaje de descuento global del comprobante
    descuento = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)

    enviado = models.BooleanField(default=False)

    data = JSONField(null=True, default=dict)

    # Un comprobante puede crearse a partir de una OrdenDeCompra
    orden_compra = models.ForeignKey('OrdenCompra', null=True, blank=True, on_delete=models.CASCADE)

    # Las NC y ND de exportacion deben informar factura E asociada
    cbte_asoc = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    @property
    def importe_neto(self):
        return sum([d.importe_neto for d in self.detallecomprobante_set.all()])

    @property
    def importe_neto_con_iva(self):
        return sum([d.precio_total for d in self.detallecomprobante_set.all()])

    @property
    def importe_neto_gravado(self):
        if self.tipo_cbte.id_afip in (
                TipoComprobante.FACTURA_C, TipoComprobante.ND_C, TipoComprobante.NC_C, TipoComprobante.RECIBO_C):
            return sum([(d.precio_unit * d.cant) for d in self.detallecomprobante_set.all()])

        return sum([d.importe_neto for d in
                    self.detallecomprobante_set.exclude(
                        alicuota_iva__id_afip__in=[AlicuotaIva.EXENTO, AlicuotaIva.NO_GRAVADO])])

    @property
    def importe_dto_neto_gravado(self):
        if self.tipo_cbte.id_afip in (
                TipoComprobante.FACTURA_C, TipoComprobante.ND_C, TipoComprobante.NC_C, TipoComprobante.RECIBO_C):
            return sum([(d.precio_unit * d.cant * -1) for d in self.detallecomprobante_set.all()
                       .filter(unidad__id_afip=Unidad.BONIFICACION_ID_AFIP)])

        return sum([d.importe_neto * -1 for d in
                    self.detallecomprobante_set.filter(unidad__id_afip=Unidad.BONIFICACION_ID_AFIP)
                   .exclude(alicuota_iva__id_afip__in=[AlicuotaIva.EXENTO, AlicuotaIva.NO_GRAVADO])])

    @property
    def importe_no_gravado(self):
        if self.tipo_cbte.id_afip in (
                TipoComprobante.FACTURA_C, TipoComprobante.ND_C, TipoComprobante.NC_C, TipoComprobante.RECIBO_C):
            return 0

        return sum([d.importe_neto for d in
                    self.detallecomprobante_set.filter(alicuota_iva__id_afip=AlicuotaIva.NO_GRAVADO)])

    @property
    def importe_dto_no_gravado(self):
        if self.tipo_cbte.id_afip in (
                TipoComprobante.FACTURA_C, TipoComprobante.ND_C, TipoComprobante.NC_C, TipoComprobante.RECIBO_C):
            return 0

        return sum([d.importe_neto * -1 for d in
                    self.detallecomprobante_set.filter(alicuota_iva__id_afip=AlicuotaIva.NO_GRAVADO,
                                                       unidad__id_afip=Unidad.BONIFICACION_ID_AFIP)])

    @property
    def importe_exento(self):
        return sum([d.importe_neto for d in
                    self.detallecomprobante_set.filter(alicuota_iva__id_afip=AlicuotaIva.EXENTO)])

    @property
    def importe_dto_exento(self):
        return sum([d.importe_neto * -1 for d in
                    self.detallecomprobante_set.filter(alicuota_iva__id_afip=AlicuotaIva.EXENTO,
                                                       unidad__id_afip=Unidad.BONIFICACION_ID_AFIP)])

    @property
    def importe_dto_neto(self):
        return self.importe_dto_exento + self.importe_dto_neto_gravado + self.importe_dto_no_gravado

    @property
    def importe_iva(self):
        if not self.muestra_alicuotas_iva():
            return 0
        return sum([(d.alicuota_iva.porc * d.precio_unit / 100) * d.cant for d in
                    self.detallecomprobante_set.exclude(
                        alicuota_iva__id_afip__in=[AlicuotaIva.EXENTO, AlicuotaIva.NO_GRAVADO])])

    @property
    def importes_ivas(self):
        ivas = {}

        for det in self.detallecomprobante_set.order_by("alicuota_iva__id_afip"):
            if det.alicuota_iva.id_afip not in (AlicuotaIva.EXENTO, AlicuotaIva.NO_GRAVADO):
                valor = (det.alicuota_iva.porc * det.precio_unit / 100) * det.cant

                if det.alicuota_iva.id in ivas:
                    ivas[det.alicuota_iva.id]["valor"] += valor
                else:
                    ivas[det.alicuota_iva.id] = {
                        "valor": valor,
                        "porc": det.alicuota_iva.porc,
                        "nombre": det.alicuota_iva.nombre
                    }

        return ivas

    @property
    def alicuotas_grouped(self):
        alicuotas = {}
        for det in self.detallecomprobante_set.order_by("alicuota_iva__id_afip"):
            if det.comprobante.es_citi_ventas():

                if det.alicuota_iva.id_afip in (
                        AlicuotaIva.EXENTO, AlicuotaIva.NO_GRAVADO) or det.comprobante.es_comprobante_e():
                    id_afip = AlicuotaIva.IVA_0
                else:
                    id_afip = det.alicuota_iva.id_afip

                if id_afip in alicuotas:
                    alicuotas[id_afip]["importe_neto_gravado"] += det.importe_neto_gravado
                else:
                    alicuotas[id_afip] = {
                        "importe_neto_gravado": det.importe_neto_gravado,
                        "porc": det.alicuota_iva.porc
                    }

        return alicuotas

    @property
    def importe_tributos(self):
        return sum([t.total for t in self.tributocomprobante_set.all()])

    @property
    def importe_tributos_nacionales(self):
        return sum([t.total for t in self.tributocomprobante_set.filter(tributo__id_afip=Tributo.NACIONALES)])

    @property
    def importe_tributos_provinciales(self):
        return sum([t.total for t in self.tributocomprobante_set.filter(tributo__id_afip=Tributo.PROVINCIALES)])

    @property
    def importe_tributos_municipales(self):
        return sum([t.total for t in self.tributocomprobante_set.filter(tributo__id_afip=Tributo.MUNICIPALES)])

    @property
    def importe_tributos_internos(self):
        return sum([t.total for t in self.tributocomprobante_set.filter(tributo__id_afip=Tributo.INTERNOS)])

    @property
    def importe_tributos_otro(self):
        return sum([t.total for t in self.tributocomprobante_set.filter(tributo__id_afip=Tributo.OTRO)])

    @property
    def importe_total(self):
        importe_detalles = sum([d.precio_total for d in self.detallecomprobante_set.all()])
        return (importe_detalles + self.importe_tributos)

    @property
    def pp_numero(self):
        if self.nro:
            return "{0:0>4}-{1:0>8}".format(self.punto_vta.id_afip, self.nro)
        return ""

    @property
    def codigo_operacion(self):
        if not self.es_citi_ventas():
            return False
        if self.es_comprobante_e():
            return "X"
        if self.importe_neto_gravado == 0:
            return "N"
        else:
            return "0"

    @property
    def mails_enviados(self):
        return self.mailenviadocomprobante_set.all().count()

    def es_factura(self):
        return self.tipo_cbte.id_afip in (
            TipoComprobante.FACTURA_A, TipoComprobante.FACTURA_B, TipoComprobante.FACTURA_C, TipoComprobante.FACTURA_E, TipoComprobante.FACTURA_M)

    def es_nota_credito(self):
        return self.tipo_cbte.id_afip in (
            TipoComprobante.NC_A, TipoComprobante.NC_B, TipoComprobante.NC_C, TipoComprobante.NC_E, TipoComprobante.NC_M)

    def es_nota_debito(self):
        return self.tipo_cbte.id_afip in (
            TipoComprobante.ND_A, TipoComprobante.ND_B, TipoComprobante.ND_C, TipoComprobante.ND_E, TipoComprobante.ND_M)

    def es_recibo(self):
        return self.tipo_cbte.id_afip in (
            TipoComprobante.RECIBO_A, TipoComprobante.RECIBO_B, TipoComprobante.RECIBO_C, TipoComprobante.RECIBO_M)

    def es_comprobante_a(self):
        return self.tipo_cbte.id_afip in (
            TipoComprobante.FACTURA_A, TipoComprobante.NC_A, TipoComprobante.ND_A, TipoComprobante.RECIBO_A)

    def es_comprobante_b(self):
        return self.tipo_cbte.id_afip in (
            TipoComprobante.FACTURA_B, TipoComprobante.NC_B, TipoComprobante.ND_B, TipoComprobante.RECIBO_B)

    def es_comprobante_c(self):
        return self.tipo_cbte.id_afip in (
            TipoComprobante.FACTURA_C, TipoComprobante.NC_C, TipoComprobante.ND_C, TipoComprobante.RECIBO_C)

    def es_comprobante_e(self):
        return self.tipo_cbte.id_afip in (
            TipoComprobante.FACTURA_E, TipoComprobante.NC_E, TipoComprobante.ND_E)

    def es_comprobante_m(self):
        return self.tipo_cbte.id_afip in (
            TipoComprobante.FACTURA_M, TipoComprobante.RECIBO_M, TipoComprobante.NC_M, TipoComprobante.ND_M)

    def esta_autorizada(self):
        return self.cae and len(self.cae) > 0

    def muestra_subtotales(self):
        return self.es_comprobante_a() or self.es_comprobante_m()

    def muestra_tributos(self):
        return self.es_comprobante_a() or self.es_comprobante_m() or self.es_comprobante_b() or self.es_comprobante_c()

    def muestra_alicuotas_iva(self):
        return self.es_comprobante_a() or self.es_comprobante_m() or self.es_comprobante_b()

    def discrimina_iva(self):
        return self.es_comprobante_a() or self.es_comprobante_m()

    def es_citi_ventas(self):
        return not self.es_comprobante_c()

    def get_data_para_imprimir(self):
        return self.get_json_data() if not self.esta_autorizada() else self.data

    def get_json_data(self):

        json_data = {
            "cae": self.cae if self.cae else "",
            "fecha_vto_cae": self.fecha_vto_cae.strftime('%d/%m/%Y') if self.fecha_vto_cae else "",
            "codigo_barras_nro": self.codigo_barras_nro,
            "empresa": {
                "nombre": self.empresa.nombre,
                "nro_doc": self.empresa.nro_doc,
                "nro_doc_formatted": self.empresa.nro_doc_formatted,
                "domicilio": self.empresa.domicilio,
                "localidad": self.empresa.localidad,
                "cod_postal": self.empresa.cod_postal,
                "email": self.empresa.email,
                "condicion_iva": self.empresa.condicion_iva.nombre,
                "es_iibb_exenta": self.empresa.es_iibb_exenta,
                "condicion_iibb": self.empresa.condicion_iibb.nombre if self.empresa.condicion_iibb else '',
                "nro_iibb": self.empresa.nro_iibb,
                "fecha_serv_desde": self.empresa.fecha_serv_desde.strftime(
                    '%d/%m/%Y') if self.empresa.fecha_serv_desde else ''
            },
            "tipo_cbte": {
                "id_afip": self.tipo_cbte.id_afip,
                "nombre": self.tipo_cbte.nombre,
                "letra": self.tipo_cbte.letra
            },
            "punto_vta": self.punto_vta.id_afip if self.punto_vta else "",
            "concepto": self.concepto.nombre if self.concepto else "",
            "nro": self.nro,
            "pp_numero": self.pp_numero,
            "condicion_venta": self.condicion_venta.nombre if self.condicion_venta else "",
            "remito_nro": self.remito_nro, "fecha_emision": self.fecha_emision.strftime('%d/%m/%Y'),
            "fecha_venc_pago": self.fecha_venc_pago.strftime('%d/%m/%Y'),
            "importe_total": str(self.importe_total),
            "importe_no_gravado": str(self.importe_no_gravado),
            "importe_dto_no_gravado": str(self.importe_dto_no_gravado),
            "importe_neto_gravado": str(self.importe_neto_gravado),
            "importe_dto_neto_gravado": str(self.importe_dto_neto_gravado),
            "importe_neto": str(self.importe_neto),
            "importe_neto_con_iva": str(self.importe_neto_con_iva),
            "importe_tributos": str(self.importe_tributos),
            "importe_exento": str(self.importe_exento),
            "importe_dto_exento": str(self.importe_dto_exento),
            "importe_iva": str(self.importe_iva),
            "cliente": {
                "tipo_doc": self.cliente.tipo_doc.nombre,
                "nro_doc": self.cliente.nro_doc,
                "nro_doc_formatted": self.cliente.nro_doc_formatted,
                "nombre": self.cliente.nombre,
                "condicion_iva": self.cliente.condicion_iva.nombre,
                "domicilio": self.cliente.domicilio,
                "localidad": self.cliente.localidad,
                "telefono": self.cliente.telefono,
                "cod_postal": self.cliente.cod_postal
            },
            "moneda": {
                "id_afip": self.moneda.id_afip,
                "nombre": self.moneda.nombre,
                "simbolo": self.moneda.simbolo
            },
            "tipo_expo": self.tipo_expo.nombre if self.tipo_expo else "",
            "incoterms": self.incoterms.id_afip if self.incoterms else "", "incoterms_ds": self.incoterms_ds,
            "idioma": self.idioma.nombre if self.idioma else "",
            "pais_destino": {
                "id_afip": self.pais_destino.id_afip if self.pais_destino else "",
                "nombre": self.pais_destino.nombre if self.pais_destino else "",
                "cuit": self.pais_destino.cuit if self.pais_destino else ""
            }, "id_impositivo": self.id_impositivo,
            "moneda_ctz": str(self.moneda_ctz),
            "observaciones_comerciales": self.observaciones_comerciales, "forma_pago": self.forma_pago,
            "condicion_venta_texto": self.condicion_venta_texto, "observaciones": self.observaciones,
            "descuento": self.descuento, "detalle": []
        }

        for detalle in self.detallecomprobante_set.all():
            json_data["detalle"].append({
                "cant": str(detalle.cant),
                "unidad": detalle.unidad.nombre,
                "detalle": detalle.detalle,
                "precio_unit": str(detalle.precio_unit),
                "alicuota_iva": {
                    "nombre": detalle.alicuota_iva.nombre if detalle.alicuota_iva else "",
                    "porc": str(detalle.alicuota_iva.porc) if detalle.alicuota_iva else ""
                }
            })

        json_data["tributos"] = []
        for tributo in self.tributocomprobante_set.all():
            json_data["tributos"].append({
                "nombre": tributo.tributo.nombre,
                "detalle": tributo.detalle,
                "base_imponible": str(tributo.base_imponible),
                "alicuota": str(tributo.alicuota)
            })

        json_data["opcionales"] = []
        for opcional in self.opcionalcomprobante_set.all():
            json_data["opcionales"].append({
                "nombre": opcional.opcional.campo,
                "valor": str(opcional.valor)
            })

        if self.cbte_asoc:
            json_data["cbte_asoc"] = {
                "tipo_cbte": {
                    "id_afip": self.cbte_asoc.tipo_cbte.id_afip,
                    "nombre": self.cbte_asoc.tipo_cbte.nombre,
                    "letra": self.cbte_asoc.tipo_cbte.letra,
                },
                "punto_vta": self.cbte_asoc.punto_vta.id_afip,
                "nro": self.cbte_asoc.nro,
                "pp_numero": self.cbte_asoc.pp_numero,
            }

        return json_data

    def set_json_data(self):
        if not self.cae:
            return
        self.data = self.get_json_data()
        self.save()

    def __str__(self):
        return self.pp_numero


class DetalleComprobante(models.Model):
    comprobante = models.ForeignKey('Comprobante', on_delete=models.CASCADE)
    producto = models.ForeignKey('empresa.Producto', null=True, blank=True, on_delete=models.CASCADE)
    cant = models.DecimalField(max_digits=19, decimal_places=2)
    detalle = models.CharField(max_length=256)
    precio_unit = models.DecimalField(max_digits=19, decimal_places=4)
    alicuota_iva = models.ForeignKey(AlicuotaIva, null=True, on_delete=models.CASCADE)
    unidad = models.ForeignKey(Unidad, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['pk']

    @property
    def importe_neto(self):
        return self.precio_unit * self.cant

    @property
    def importe_iva(self):
        if not self.alicuota_iva:
            return self.precio_unit * self.cant
        return (self.precio_unit * self.alicuota_iva.porc / 100) * Decimal(self.cant)

    @property
    def precio_unitario_con_iva(self):
        if not self.alicuota_iva:
            return self.precio_unit
        return (self.precio_unit + (self.precio_unit * self.alicuota_iva.porc / 100))

    @property
    def precio_total(self):
        return self.precio_unitario_con_iva * Decimal(self.cant)

    @property
    def importe_neto_gravado(self):
        if self.alicuota_iva.id_afip in (AlicuotaIva.EXENTO, AlicuotaIva.NO_GRAVADO):
            return 0
        else:
            return self.importe_neto

    @property
    def citi_alicuota_id_afip(self):
        if self.comprobante.es_comprobante_e() or self.importe_neto_gravado == 0:
            return 0
        else:
            return self.alicuota_iva.id_afip


class TributoComprobante(models.Model):
    comprobante = models.ForeignKey('Comprobante', on_delete=models.CASCADE)
    tributo = models.ForeignKey(Tributo, on_delete=models.CASCADE)
    detalle = models.CharField(max_length=256, null=True, blank=True)
    base_imponible = models.DecimalField(max_digits=19, decimal_places=4)
    alicuota = models.DecimalField(max_digits=19, decimal_places=4)

    @property
    def total(self):
        return self.base_imponible * self.alicuota / 100


class OpcionalComprobante(models.Model):
    comprobante = models.ForeignKey('Comprobante', on_delete=models.CASCADE)
    opcional = models.ForeignKey(Opcional, on_delete=models.CASCADE)
    valor = models.CharField(max_length=256, null=True, blank=True)

    @property
    def valor_formateado(self):
        if self.opcional.tiene_opciones:
            opcion = self.opcional.opcionopcional_set.filter(valor=self.valor).first()
            return opcion.descripcion
        return self.valor


class MailEnviadoComprobante(models.Model):
    comprobante = models.ForeignKey('Comprobante', on_delete=models.CASCADE)
    email = models.EmailField(max_length=256)
    fecha_envio = models.DateTimeField(default=datetime.date.today)
    estado = models.CharField(max_length=256)
    texto = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)


class ComprobanteNA(BajaLogicaClass):
    nro = models.IntegerField(null=True)
    fecha_emision = models.DateField(default=datetime.date.today)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    # Datos de emisor y receptor de un CbteNA para que al momento del parseo automatico de EDI
    # se puedan almacenar sus valores (en memoria) y luego ser utilizados para la persistencia final del Cbte
    cuit_emisor_eancom = None
    cuit_receptor_eancom = None

    tributo = models.ForeignKey('TributoComprobanteNA', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @property
    def importe_no_gravado(self):
        return sum([d.importe_neto for d in
                    self.detalleordencompra_set.filter(alicuota_iva__id_afip=AlicuotaIva.NO_GRAVADO)])

    @property
    def importe_exento(self):
        return sum([d.importe_neto for d in
                    self.detalleordencompra_set.filter(alicuota_iva__id_afip=AlicuotaIva.EXENTO)])

    @property
    def importe_neto_gravado(self):
        return sum([(d.precio_unit * d.cantidad_pedida) for d in self.detalleordencompra_set.all()])

    @property
    def importe_total(self):
        if self.tributo:
            return self.importe_neto_gravado + self.importe_iva + self.tributo.total
        return self.importe_neto_gravado + self.importe_iva

    @property
    def importe_iva(self):
        detalles_con_iva = self.detalleordencompra_set.exclude(producto__alicuota_iva=None)
        return sum([(d.producto.alicuota_iva.porc * d.precio_unit / 100) * d.cantidad_pedida for d in
                    detalles_con_iva.exclude(producto__alicuota_iva__id_afip__in=[AlicuotaIva.EXENTO, AlicuotaIva.NO_GRAVADO])])

    @property
    def has_productos_from_edi(self):
        return self.detalleordencompra_set.filter(producto__alta_edi=True).exists()

    @property
    def importes_ivas(self):
        ivas = {}
        for det in self.detalleordencompra_set.order_by("alicuota_iva__id_afip"):
            if det.alicuota_iva.id_afip not in (AlicuotaIva.EXENTO, AlicuotaIva.NO_GRAVADO):
                valor = (det.alicuota_iva.porc * det.precio_unit / 100) * det.cantidad_pedida
                if det.alicuota_iva.id in ivas:
                    ivas[det.alicuota_iva.id]["valor"] += valor
                else:
                    ivas[det.alicuota_iva.id] = {
                        "valor": valor,
                        "porc": det.alicuota_iva.porc,
                        "nombre": det.alicuota_iva.nombre
                    }

        return ivas


class DetalleComprobanteNA(models.Model):
    detalle = models.CharField(max_length=256)
    precio_unit = models.DecimalField(max_digits=19, decimal_places=4)
    alicuota_iva = models.ForeignKey(AlicuotaIva, null=True, blank=True, on_delete=models.CASCADE)
    producto = models.ForeignKey('empresa.Producto', null=True, blank=True, on_delete=models.CASCADE)
    unidad = models.ForeignKey(Unidad, null=True, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class OrdenCompra(ComprobanteNA):
    fecha_entrega_estimada = models.DateField(default=venc_default)
    fecha_entrega_limite = models.DateField(default=venc_default)

    gln_lugar_entrega = models.CharField(max_length=128, null=True, blank=True)
    lugar_entrega = models.CharField(max_length=256, null=True, blank=True)

    # nro proveedor que posee internamente la cadena de retail o agente edi
    nro_proveedor_retail = models.CharField(max_length=128)
    # codigo GLN que identifica al agente EDI
    codigo_gln_retail = models.CharField(max_length=128)
    # codigo GLN del proveedor del agente edi, es decir del usuario Pirra
    codigo_gln_proveedor = models.CharField(max_length=128)

    INGRESADA  = "INGR"
    PENDIENTE = "PEND"
    VENCIDA = "VENC"
    CUMPLIDA = "CUMP"
    EstadoOrdenCompra = (
        (INGRESADA, "Ingresada"),
        (PENDIENTE, "Pendiente"),
        (VENCIDA, "Vencida"),
        (CUMPLIDA, "Cumplida"),
    )

    estado = models.CharField(max_length=4, choices=EstadoOrdenCompra, default=INGRESADA)

    @property
    def is_completed(self):
        return self.estado == self.CUMPLIDA

    @property
    def has_expired(self):
        return self.estado == self.VENCIDA

    def __str__(self):
        return str(self.nro)


class DetalleOrdenCompra(DetalleComprobanteNA):
    orden_compra = models.ForeignKey('OrdenCompra', on_delete=models.CASCADE)
    codigo_proveedor_articulo = models.CharField(max_length=128, blank=True)
    cantidad_cajas = models.IntegerField(blank=True, null=True)
    unidades_x_caja = models.IntegerField(blank=True, null=True)

    cantidad = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)

    @property
    def precio_unitario_con_iva(self):
        if not self.producto.alicuota_iva:
            return self.precio_unit
        return Decimal(self.precio_unit) + (Decimal(self.precio_unit) * self.producto.alicuota_iva.porc / 100)

    @property
    def precio_total(self):
        return Decimal(self.precio_unitario_con_iva) * Decimal(self.cantidad_pedida)

    @property
    def cantidad_pedida(self):
        if self.unidad.id_afip == Unidad.UNIDADES_ID_AFIP:
            return self.unidades_x_caja * self.cantidad_cajas
        return self.cantidad


class TributoComprobanteNA(models.Model):
    tributo = models.ForeignKey(Tributo, on_delete=models.CASCADE)
    detalle = models.CharField(max_length=256, null=True, blank=True)
    base_imponible = models.DecimalField(max_digits=19, decimal_places=4)
    alicuota = models.DecimalField(max_digits=19, decimal_places=4)

    @property
    def total(self):
        return self.base_imponible * self.alicuota / 100