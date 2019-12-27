from decimal import Decimal
from afip.models import AlicuotaIva, TipoComprobante, Opcional, ResolucionGeneral
from comprobante.models import Comprobante, DetalleComprobante, TributoComprobante, OpcionalComprobante, MailEnviadoComprobante
from django.urls import reverse
from datetime import date
from empresa.models import Empresa, Cliente, PuntoDeVenta

__author__ = 'mlambir'

def crear_empresa():
    empresa = Empresa(
        nombre="Empresa A", nro_doc="11111111111", email="info@info.com", domicilio="Calle", localidad="CABA", cod_postal="1416",
        condicion_iva_id=3, condicion_iibb_id=3, nro_iibb="", fecha_serv_desde=date.today()
    )
    empresa.save()
    return empresa

def crear_cliente():
    cliente = Cliente(
        tipo_doc_id=1, nro_doc="123", nombre="cliente test", condicion_iva_id=3, domicilio="Altoro 54", localidad="CABA", telefono="1234",
        cod_postal="", email="cli@cli.com"
    )
    cliente.save()
    return cliente

def crear_punto_vta():
    punto_vta = PuntoDeVenta(id_afip=1, nombre="punto 1")
    punto_vta.save()
    return punto_vta

def crear_resolucion_general():
    resolucion = ResolucionGeneral(numero=1, nombre="Resolucion 1")
    resolucion.save()
    return  resolucion

def crear_opcional(resolucion_gral, nombre_campo):
    opcional = Opcional(id_afip=1, resolucion_general=resolucion_gral, campo=nombre_campo)
    opcional.save()
    return opcional

def crear_comprobante(empresa, cliente, punto_vta, opcionales):
    today = date.today()

    comprobante = Comprobante(cae="12344321", nro=1, empresa=empresa, cliente=cliente, fecha_vto_cae=today, fecha_emision=today, codigo_barras_nro="1234",
       tipo_cbte_id=1, punto_vta=punto_vta, concepto_id=2, remito_nro="123", fecha_venc_pago=today, moneda_id=1, condicion_venta_id=1)
    comprobante.save()

    detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=10, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
    detalle.save()

    tributo = TributoComprobante(comprobante_id=comprobante.pk, tributo_id=1, detalle="item", base_imponible=10, alicuota=3.5)
    tributo.save()

    idx = 0
    for opcional in opcionales:
        opcional_cbte = OpcionalComprobante(comprobante=comprobante, opcional=opcional, valor=idx)
        opcional_cbte.save()
        idx += 1

    return comprobante

def crear_comprobante_e(empresa, cliente, punto_vta):
    today = date.today()

    comprobante = Comprobante(cae="12344441", nro=1, empresa=empresa, cliente=cliente, fecha_vto_cae=today, fecha_emision=today, codigo_barras_nro="1234",
       tipo_cbte_id=9, punto_vta=punto_vta, concepto_id=2, remito_nro="123", fecha_venc_pago=today, moneda_id=2, condicion_venta_id=1,
       tipo_expo_id=2, idioma_id=1, incoterms_id=1, pais_destino_id=1, id_impositivo="123", moneda_ctz=10.00,
       observaciones_comerciales="obs com", forma_pago="transfer", incoterms_ds="ws", condicion_venta_texto="transfer")
    comprobante.save()

    detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item for export", precio_unit=50, unidad_id=2)
    detalle.save()

    return comprobante

def get_comprobante(empresa, cliente, punto_vta, tipo_cbte):
    today = date.today()

    return Comprobante(cae="12344321", nro=1, empresa=empresa, cliente=cliente, fecha_vto_cae=today, fecha_emision=today, codigo_barras_nro="1234",
       tipo_cbte_id=tipo_cbte, punto_vta=punto_vta, concepto_id=2, remito_nro="123", fecha_venc_pago=today, moneda_id=1, condicion_venta_id=1)


class TestComprobantes():
    def setUp(self):
        self.c = TenantClient(self.tenant)
        self.c.login(username="test_admin", password="test_admin")

        self.empresa = crear_empresa()
        self.cliente = crear_cliente()
        self.punto_vta = crear_punto_vta()
        self.resolucion_general = crear_resolucion_general()
        self.opcionales = [crear_opcional(self.resolucion_general, "Campo 1"), crear_opcional(self.resolucion_general, "Campo 2")]
        self.comprobante = crear_comprobante(self.empresa, self.cliente, self.punto_vta, self.opcionales)
        self.comprobante_e = crear_comprobante_e(self.empresa, self.cliente, self.punto_vta)

    def test_comprobante_list_view(self):
        response = self.c.get(reverse('comprobante.list'))
        self.assertEqual(response.status_code, 200)

    def test_comprobante_importe_neto(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()

        self.assertEqual(comprobante.importe_neto, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=10, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=10, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_neto, 0+20)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=15, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_neto, 20+30)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_neto, 50+150)

        tributo = TributoComprobante(comprobante_id=comprobante.pk, tributo_id=1, detalle="item", base_imponible=100, alicuota=3)
        tributo.save()
        self.assertEqual(comprobante.importe_neto, 50+150) # el tributo no afecta el importe neto

    def test_comprobante_importe_exento(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()

        self.assertEqual(comprobante.importe_exento, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=10, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=10, alicuota_iva_id=AlicuotaIva.IVA_5_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_exento, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=15, alicuota_iva_id=AlicuotaIva.EXENTO_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_exento, 15*2)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.EXENTO_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_exento, 30+100*1.5)

    def test_comprobante_importe_iva(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()

        self.assertEqual(comprobante.importe_iva, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_5_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_iva, 21+5)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=15, alicuota_iva_id=AlicuotaIva.EXENTO_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_iva, 26)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=15, alicuota_iva_id=AlicuotaIva.NO_GRAVADO_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_iva, 26)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=15, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_iva, 26)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_27_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_iva, 26+2*27)

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_E_PK)
        comprobante.save()

        self.assertEqual(comprobante.importe_iva, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_5_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.importe_iva, 0)

    def test_comprobante_importes_ivas(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()

        self.assertEqual(comprobante.importes_ivas, {})

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_5_PK, unidad_id=2)
        detalle.save()

        resultado = {}
        resultado[AlicuotaIva.IVA_21_PK] = {
            "valor": 21,
            "porc": 21,
            "nombre": "IVA"
        }
        resultado[AlicuotaIva.IVA_5_PK] = {
            "valor": 5,
            "porc": 5,
            "nombre": "IVA"
        }
        self.assertEqual(comprobante.importes_ivas, resultado)

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.EXENTO_PK, unidad_id=2)
        detalle.save()

        self.assertEqual(comprobante.importes_ivas, {})

    def test_comprobante_pp_numero(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        self.assertEqual(comprobante.pp_numero, "0001-00000001")

    def test_comprobante_importe_neto_con_iva(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()

        self.assertEqual(comprobante.importe_neto_con_iva, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=10, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=10, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        self.assertAlmostEqual(comprobante.importe_neto_con_iva, Decimal(0+12.1+12.1), places=7, msg=None, delta=None)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=15, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        self.assertAlmostEqual(comprobante.importe_neto_con_iva, Decimal((12.1+12.1)+(2*15*1.21)), places=7, msg=None, delta=None)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        self.assertAlmostEqual(comprobante.importe_neto_con_iva, Decimal((12.1+12.1)+(2*15*1.21)+(1.5*121)), places=7, msg=None, delta=None)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        detalle.save()
        self.assertAlmostEqual(comprobante.importe_neto_con_iva, Decimal((12.1+12.1)+(2*15*1.21)+(1.5*121)+100), places=7, msg=None, delta=None)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1, detalle="item", precio_unit=80, alicuota_iva_id=AlicuotaIva.IVA_5_PK, unidad_id=2)
        detalle.save()
        self.assertAlmostEqual(comprobante.importe_neto_con_iva, Decimal((12.1+12.1)+(2*15*1.21)+(1.5*121)+100+80*1.05), places=7, msg=None, delta=None)

    def test_comprobante_importe_tributos(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()

        tributo1 = TributoComprobante(comprobante_id=comprobante.pk, tributo_id=1, detalle="item", base_imponible=100, alicuota=3)
        tributo1.save()
        tributo2 = TributoComprobante(comprobante_id=comprobante.pk, tributo_id=2, detalle="item", base_imponible=200, alicuota=50)
        tributo2.save()

        self.assertAlmostEqual(comprobante.importe_tributos, 3+100, places=7, msg=None, delta=None)

    def test_comprobante_es_factura(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        self.assertTrue(comprobante.es_factura())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_B_PK)
        self.assertTrue(comprobante.es_factura())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_C_PK)
        self.assertTrue(comprobante.es_factura())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_E_PK)
        self.assertTrue(comprobante.es_factura())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.RECIBO_B_PK)
        self.assertFalse(comprobante.es_factura())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.ND_B_PK)
        self.assertFalse(comprobante.es_factura())

    def test_comprobante_esta_autorizada(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        self.assertTrue(comprobante.esta_autorizada())
        comprobante.cae = None
        self.assertFalse(comprobante.esta_autorizada())
        comprobante.cae = ""
        self.assertFalse(comprobante.esta_autorizada())

    def test_comprobante_muestra_subtotales(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        self.assertTrue(comprobante.muestra_subtotales())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.ND_A_PK)
        self.assertTrue(comprobante.muestra_subtotales())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.NC_A_PK)
        self.assertTrue(comprobante.muestra_subtotales())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_E_PK)
        self.assertFalse(comprobante.muestra_subtotales())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_B_PK)
        self.assertFalse(comprobante.muestra_subtotales())

    def test_comprobante_muestra_tributos(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        self.assertTrue(comprobante.muestra_tributos())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.ND_A_PK)
        self.assertTrue(comprobante.muestra_tributos())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.NC_A_PK)
        self.assertTrue(comprobante.muestra_tributos())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_E_PK)
        self.assertFalse(comprobante.muestra_tributos())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_B_PK)
        self.assertTrue(comprobante.muestra_tributos())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.NC_B_PK)
        self.assertTrue(comprobante.muestra_tributos())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.RECIBO_B_PK)
        self.assertTrue(comprobante.muestra_tributos())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_C_PK)
        self.assertTrue(comprobante.muestra_tributos())

    def test_comprobante_muestra_alicuotas_iva(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        self.assertTrue(comprobante.muestra_alicuotas_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.ND_A_PK)
        self.assertTrue(comprobante.muestra_alicuotas_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.NC_A_PK)
        self.assertTrue(comprobante.muestra_alicuotas_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_E_PK)
        self.assertFalse(comprobante.muestra_alicuotas_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_B_PK)
        self.assertTrue(comprobante.muestra_alicuotas_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.NC_B_PK)
        self.assertTrue(comprobante.muestra_alicuotas_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.RECIBO_B_PK)
        self.assertTrue(comprobante.muestra_alicuotas_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_C_PK)
        self.assertFalse(comprobante.muestra_alicuotas_iva())

    def test_comprobante_discrimina_iva(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        self.assertTrue(comprobante.discrimina_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.ND_A_PK)
        self.assertTrue(comprobante.discrimina_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.NC_A_PK)
        self.assertTrue(comprobante.discrimina_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_E_PK)
        self.assertFalse(comprobante.discrimina_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_B_PK)
        self.assertFalse(comprobante.discrimina_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.NC_B_PK)
        self.assertFalse(comprobante.discrimina_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.RECIBO_B_PK)
        self.assertFalse(comprobante.discrimina_iva())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_C_PK)
        self.assertFalse(comprobante.discrimina_iva())

    def test_comprobante_es_citi_ventas(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        self.assertTrue(comprobante.es_citi_ventas())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.ND_A_PK)
        self.assertTrue(comprobante.es_citi_ventas())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.NC_A_PK)
        self.assertTrue(comprobante.es_citi_ventas())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_E_PK)
        self.assertTrue(comprobante.es_citi_ventas())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_B_PK)
        self.assertTrue(comprobante.es_citi_ventas())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.NC_B_PK)
        self.assertTrue(comprobante.es_citi_ventas())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.RECIBO_B_PK)
        self.assertTrue(comprobante.es_citi_ventas())

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_C_PK)
        self.assertFalse(comprobante.es_citi_ventas())

    def test_comprobante_get_data_para_imprimir(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.data = "{ foo: bar }"
        self.assertEqual(comprobante.get_data_para_imprimir(), comprobante.data)
        comprobante.set_json_data()
        self.assertEqual(comprobante.get_data_para_imprimir(), comprobante.data)

    def test_comprobante_codigo_operacion(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_C_PK)
        self.assertFalse(comprobante.codigo_operacion)

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_E_PK)
        self.assertEqual(comprobante.codigo_operacion, "X")

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()
        self.assertEqual(comprobante.codigo_operacion, "N")

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        detalle.save()
        self.assertEqual(comprobante.codigo_operacion, "0")

    def test_comprobante_set_json_data(self):
        cbte = self.comprobante
        cbte.set_json_data()
        self.assertEqual(cbte.data["cae"], cbte.cae)
        self.assertEqual(cbte.data["fecha_vto_cae"], cbte.fecha_vto_cae.strftime('%d/%m/%Y'))
        self.assertEqual(cbte.data["codigo_barras_nro"], cbte.codigo_barras_nro)
        self.assertEqual(cbte.data["empresa"]["nombre"], cbte.empresa.nombre)
        self.assertEqual(cbte.data["empresa"]["nro_doc"], cbte.empresa.nro_doc)
        self.assertEqual(cbte.data["empresa"]["nro_doc_formatted"], cbte.empresa.nro_doc_formatted)
        self.assertEqual(cbte.data["empresa"]["domicilio"], cbte.empresa.domicilio)
        self.assertEqual(cbte.data["empresa"]["localidad"], cbte.empresa.localidad)
        self.assertEqual(cbte.data["empresa"]["cod_postal"], cbte.empresa.cod_postal)
        self.assertEqual(cbte.data["empresa"]["email"], cbte.empresa.email)
        self.assertEqual(cbte.data["empresa"]["condicion_iva"], cbte.empresa.condicion_iva.nombre)
        self.assertEqual(cbte.data["empresa"]["es_iibb_exenta"], cbte.empresa.es_iibb_exenta)
        self.assertEqual(cbte.data["empresa"]["condicion_iibb"], cbte.empresa.condicion_iibb.nombre)
        self.assertEqual(cbte.data["empresa"]["nro_iibb"], cbte.empresa.nro_iibb)
        self.assertEqual(cbte.data["empresa"]["fecha_serv_desde"], cbte.empresa.fecha_serv_desde.strftime('%d/%m/%Y'))
        self.assertEqual(cbte.data["tipo_cbte"]["id_afip"], cbte.tipo_cbte.id_afip)
        self.assertEqual(cbte.data["tipo_cbte"]["nombre"], cbte.tipo_cbte.nombre)
        self.assertEqual(cbte.data["tipo_cbte"]["letra"], cbte.tipo_cbte.letra)
        self.assertEqual(cbte.data["punto_vta"], cbte.punto_vta.id_afip)
        self.assertEqual(cbte.data["concepto"], cbte.concepto.nombre)
        self.assertEqual(cbte.data["nro"], cbte.nro)
        self.assertEqual(cbte.data["pp_numero"], cbte.pp_numero)
        self.assertEqual(cbte.data["condicion_venta"], cbte.condicion_venta.nombre)
        self.assertEqual(cbte.data["remito_nro"], cbte.remito_nro)
        self.assertEqual(cbte.data["fecha_emision"], cbte.fecha_emision.strftime('%d/%m/%Y'))
        self.assertEqual(cbte.data["fecha_venc_pago"], cbte.fecha_venc_pago.strftime('%d/%m/%Y'))
        self.assertEqual(cbte.data["importe_total"], cbte.importe_total)
        self.assertEqual(cbte.data["importe_no_gravado"], cbte.importe_no_gravado)
        self.assertEqual(cbte.data["importe_neto"], cbte.importe_neto)
        self.assertEqual(cbte.data["importe_neto_gravado"], cbte.importe_neto_gravado)
        self.assertEqual(cbte.data["importe_neto_con_iva"], cbte.importe_neto_con_iva)
        self.assertEqual(cbte.data["importe_tributos"], cbte.importe_tributos)
        self.assertEqual(cbte.data["importe_exento"], cbte.importe_exento)
        self.assertEqual(cbte.data["importe_iva"], cbte.importe_iva)
        self.assertEqual(cbte.data["cliente"]["tipo_doc"], cbte.cliente.tipo_doc.nombre)
        self.assertEqual(cbte.data["cliente"]["nro_doc"], cbte.cliente.nro_doc)
        self.assertEqual(cbte.data["cliente"]["nro_doc_formatted"], cbte.cliente.nro_doc_formatted)
        self.assertEqual(cbte.data["cliente"]["nombre"], cbte.cliente.nombre)
        self.assertEqual(cbte.data["cliente"]["condicion_iva"], cbte.cliente.condicion_iva.nombre)
        self.assertEqual(cbte.data["cliente"]["domicilio"], cbte.cliente.domicilio)
        self.assertEqual(cbte.data["cliente"]["localidad"], cbte.cliente.localidad)
        self.assertEqual(cbte.data["cliente"]["telefono"], cbte.cliente.telefono)
        self.assertEqual(cbte.data["cliente"]["cod_postal"], cbte.cliente.cod_postal)
        self.assertEqual(cbte.data["moneda"]["id_afip"], cbte.moneda.id_afip)
        self.assertEqual(cbte.data["moneda"]["nombre"], cbte.moneda.nombre)
        self.assertEqual(cbte.data["moneda"]["simbolo"], cbte.moneda.simbolo)
        self.assertEqual(cbte.data["observaciones"], cbte.observaciones)
        i = 0
        for detalle in cbte.detallecomprobante_set.all():
            self.assertEqual(cbte.data["detalle"][i]["cant"], detalle.cant)
            self.assertEqual(cbte.data["detalle"][i]["unidad"], detalle.unidad.nombre)
            self.assertEqual(cbte.data["detalle"][i]["detalle"], detalle.detalle)
            self.assertEqual(cbte.data["detalle"][i]["precio_unit"], detalle.precio_unit)
            self.assertEqual(cbte.data["detalle"][i]["alicuota_iva"]["nombre"], detalle.alicuota_iva.nombre)
            self.assertEqual(cbte.data["detalle"][i]["alicuota_iva"]["porc"], detalle.alicuota_iva.porc)
            i+=1
        i = 0
        for tributo in cbte.tributocomprobante_set.all():
            self.assertEqual(cbte.data["tributos"][i]["nombre"], tributo.tributo.nombre)
            self.assertEqual(cbte.data["tributos"][i]["detalle"], tributo.detalle)
            self.assertEqual(cbte.data["tributos"][i]["base_imponible"], tributo.base_imponible)
            self.assertEqual(cbte.data["tributos"][i]["alicuota"], tributo.alicuota)
            i+=1
        i = 0
        for opcional in cbte.opcionalcomprobante_set.all():
            self.assertEqual(cbte.data["opcionales"][i]["nombre"], opcional.opcional.campo)
            self.assertEqual(cbte.data["opcionales"][i]["valor"], opcional.valor)
            i+=1

    def test_comprobante_exportacion_set_json_data(self):
        cbte = self.comprobante_e
        cbte.set_json_data()
        self.assertEqual(cbte.data["cae"], cbte.cae)
        self.assertEqual(cbte.data["fecha_vto_cae"], cbte.fecha_vto_cae.strftime('%d/%m/%Y'))
        self.assertEqual(cbte.data["codigo_barras_nro"], cbte.codigo_barras_nro)
        self.assertEqual(cbte.data["empresa"]["nombre"], cbte.empresa.nombre)
        self.assertEqual(cbte.data["empresa"]["nro_doc"], cbte.empresa.nro_doc)
        self.assertEqual(cbte.data["empresa"]["nro_doc_formatted"], cbte.empresa.nro_doc_formatted)
        self.assertEqual(cbte.data["empresa"]["domicilio"], cbte.empresa.domicilio)
        self.assertEqual(cbte.data["empresa"]["localidad"], cbte.empresa.localidad)
        self.assertEqual(cbte.data["empresa"]["cod_postal"], cbte.empresa.cod_postal)
        self.assertEqual(cbte.data["empresa"]["email"], cbte.empresa.email)
        self.assertEqual(cbte.data["empresa"]["condicion_iva"], cbte.empresa.condicion_iva.nombre)
        self.assertEqual(cbte.data["empresa"]["es_iibb_exenta"], cbte.empresa.es_iibb_exenta)
        self.assertEqual(cbte.data["empresa"]["condicion_iibb"], cbte.empresa.condicion_iibb.nombre)
        self.assertEqual(cbte.data["empresa"]["nro_iibb"], cbte.empresa.nro_iibb)
        self.assertEqual(cbte.data["empresa"]["fecha_serv_desde"], cbte.empresa.fecha_serv_desde.strftime('%d/%m/%Y'))
        self.assertEqual(cbte.data["tipo_cbte"]["id_afip"], cbte.tipo_cbte.id_afip)
        self.assertEqual(cbte.data["tipo_cbte"]["nombre"], cbte.tipo_cbte.nombre)
        self.assertEqual(cbte.data["tipo_cbte"]["letra"], cbte.tipo_cbte.letra)
        self.assertEqual(cbte.data["punto_vta"], cbte.punto_vta.id_afip)
        self.assertEqual(cbte.data["concepto"], cbte.concepto.nombre)
        self.assertEqual(cbte.data["nro"], cbte.nro)
        self.assertEqual(cbte.data["pp_numero"], cbte.pp_numero)
        self.assertEqual(cbte.data["condicion_venta"], cbte.condicion_venta.nombre)
        self.assertEqual(cbte.data["remito_nro"], cbte.remito_nro)
        self.assertEqual(cbte.data["fecha_emision"], cbte.fecha_emision.strftime('%d/%m/%Y'))
        self.assertEqual(cbte.data["fecha_venc_pago"], cbte.fecha_venc_pago.strftime('%d/%m/%Y'))
        self.assertEqual(cbte.data["importe_total"], cbte.importe_total)
        self.assertEqual(cbte.data["importe_no_gravado"], cbte.importe_no_gravado)
        self.assertEqual(cbte.data["importe_neto"], cbte.importe_neto)
        self.assertEqual(cbte.data["importe_neto_gravado"], cbte.importe_neto_gravado)
        self.assertEqual(cbte.data["importe_neto_con_iva"], cbte.importe_neto_con_iva)
        self.assertEqual(cbte.data["importe_tributos"], cbte.importe_tributos)
        self.assertEqual(cbte.data["importe_exento"], cbte.importe_exento)
        self.assertEqual(cbte.data["importe_iva"], cbte.importe_iva)
        self.assertEqual(cbte.data["cliente"]["tipo_doc"], cbte.cliente.tipo_doc.nombre)
        self.assertEqual(cbte.data["cliente"]["nro_doc"], cbte.cliente.nro_doc)
        self.assertEqual(cbte.data["cliente"]["nro_doc_formatted"], cbte.cliente.nro_doc_formatted)
        self.assertEqual(cbte.data["cliente"]["nombre"], cbte.cliente.nombre)
        self.assertEqual(cbte.data["cliente"]["condicion_iva"], cbte.cliente.condicion_iva.nombre)
        self.assertEqual(cbte.data["cliente"]["domicilio"], cbte.cliente.domicilio)
        self.assertEqual(cbte.data["cliente"]["localidad"], cbte.cliente.localidad)
        self.assertEqual(cbte.data["cliente"]["telefono"], cbte.cliente.telefono)
        self.assertEqual(cbte.data["cliente"]["cod_postal"], cbte.cliente.cod_postal)
        self.assertEqual(cbte.data["moneda"]["id_afip"], cbte.moneda.id_afip)
        self.assertEqual(cbte.data["moneda"]["nombre"], cbte.moneda.nombre)
        self.assertEqual(cbte.data["moneda"]["simbolo"], cbte.moneda.simbolo)
        self.assertEqual(cbte.data["observaciones"], cbte.observaciones)
        self.assertEqual(cbte.data["tipo_expo"], cbte.tipo_expo.nombre)
        self.assertEqual(cbte.data["incoterms"], cbte.incoterms.id_afip)
        self.assertEqual(cbte.data["incoterms_ds"], cbte.incoterms_ds)
        self.assertEqual(cbte.data["idioma"], cbte.idioma.nombre)
        self.assertEqual(cbte.data["pais_destino"]["id_afip"], cbte.pais_destino.id_afip)
        self.assertEqual(cbte.data["pais_destino"]["nombre"], cbte.pais_destino.nombre)
        self.assertEqual(cbte.data["pais_destino"]["cuit"], cbte.pais_destino.cuit)
        self.assertEqual(cbte.data["id_impositivo"], cbte.id_impositivo)
        self.assertEqual(cbte.data["moneda_ctz"], cbte.moneda_ctz)
        self.assertEqual(cbte.data["observaciones_comerciales"], cbte.observaciones_comerciales)
        self.assertEqual(cbte.data["forma_pago"], cbte.forma_pago)
        self.assertEqual(cbte.data["condicion_venta_texto"], cbte.condicion_venta_texto)
        i = 0
        for detalle in cbte.detallecomprobante_set.all():
            self.assertEqual(cbte.data["detalle"][i]["cant"], detalle.cant)
            self.assertEqual(cbte.data["detalle"][i]["unidad"], detalle.unidad.nombre)
            self.assertEqual(cbte.data["detalle"][i]["detalle"], detalle.detalle)
            self.assertEqual(cbte.data["detalle"][i]["precio_unit"], detalle.precio_unit)
            self.assertEqual(cbte.data["detalle"][i]["alicuota_iva"]["nombre"], "")
            self.assertEqual(cbte.data["detalle"][i]["alicuota_iva"]["porc"], "")
            i+=1


    def test_detalle_comprobante_importe_neto(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        self.assertEqual(detalle.importe_neto, 150)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        self.assertEqual(detalle.importe_neto, 200)

    def test_detalle_comprobante_importe_iva(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.NO_GRAVADO_PK, unidad_id=2)
        self.assertEqual(detalle.importe_iva, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)

        self.assertEqual(detalle.importe_iva, 1.5*21)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        self.assertEqual(detalle.importe_iva, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.EXENTO_PK, unidad_id=2)
        self.assertEqual(detalle.importe_iva, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_10_5_PK, unidad_id=2)
        self.assertEqual(detalle.importe_iva, 2*10.5)

    def test_detalle_comprobante_precio_unitario_con_iva(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        self.assertEqual(detalle.precio_unitario_con_iva, 100)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        self.assertEqual(detalle.precio_unitario_con_iva, 121)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        self.assertEqual(detalle.precio_unitario_con_iva, 121)

    def test_detalle_comprobante_precio_total(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        self.assertEqual(detalle.precio_total, 1.5*100)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        self.assertEqual(detalle.precio_total, 1.5*121)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        self.assertEqual(detalle.precio_total, 2*121)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=1, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        self.assertEqual(detalle.precio_total, 2*1)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=1, alicuota_iva_id=AlicuotaIva.EXENTO_PK, unidad_id=2)
        self.assertEqual(detalle.precio_total, 2*1)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=1, alicuota_iva_id=AlicuotaIva.NO_GRAVADO_PK, unidad_id=2)
        self.assertEqual(detalle.precio_total, 2*1)

    def test_detalle_comprobante_importe_neto_gravado(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        self.assertEqual(detalle.importe_neto_gravado, 1.5*100)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        self.assertEqual(detalle.importe_neto_gravado, 1.5*100)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        self.assertEqual(detalle.importe_neto_gravado, 2*100)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=1, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        self.assertEqual(detalle.importe_neto_gravado, 2*1)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=1, alicuota_iva_id=AlicuotaIva.EXENTO_PK, unidad_id=2)
        self.assertEqual(detalle.importe_neto_gravado, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=1, alicuota_iva_id=AlicuotaIva.NO_GRAVADO_PK, unidad_id=2)
        self.assertEqual(detalle.importe_neto_gravado, 0)

    def test_detalle_comprobante_citi_alicuota_id_afip(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_E_PK)
        comprobante.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        self.assertEqual(detalle.citi_alicuota_id_afip, 0)

        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()
        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=1.5, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.EXENTO_PK, unidad_id=2)
        self.assertEqual(detalle.citi_alicuota_id_afip, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=100, alicuota_iva_id=AlicuotaIva.IVA_21_PK, unidad_id=2)
        self.assertEqual(detalle.citi_alicuota_id_afip, detalle.alicuota_iva.id_afip)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=1, alicuota_iva_id=AlicuotaIva.IVA_0_PK, unidad_id=2)
        self.assertEqual(detalle.citi_alicuota_id_afip, detalle.alicuota_iva.id_afip)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=1, alicuota_iva_id=AlicuotaIva.NO_GRAVADO_PK, unidad_id=2)
        self.assertEqual(detalle.citi_alicuota_id_afip, 0)

        detalle = DetalleComprobante(comprobante_id=comprobante.pk, cant=2, detalle="item", precio_unit=1, alicuota_iva_id=AlicuotaIva.IVA_27_PK, unidad_id=2)
        self.assertEqual(detalle.citi_alicuota_id_afip, detalle.alicuota_iva.id_afip)

    def test_tributo_comprobante_total(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        tributo = TributoComprobante(comprobante_id=comprobante.pk, tributo_id=1, detalle="item", base_imponible=10, alicuota=3.5)
        self.assertEqual(tributo.total, 10*3.5/100)

        tributo = TributoComprobante(comprobante_id=comprobante.pk, tributo_id=2, detalle="item", base_imponible=50, alicuota=5)
        self.assertEqual(tributo.total, 50*5/100)


    def test_comprobante_mails_enviados(self):
        comprobante = get_comprobante(self.empresa, self.cliente, self.punto_vta, TipoComprobante.FACTURA_A_PK)
        comprobante.save()
        self.assertEqual(comprobante.mails_enviados, 0)

        mail = MailEnviadoComprobante(comprobante=comprobante, email="person@pirra.coop", fecha_envio=date.today(),
            estado="Ok", texto="")
        mail.save()
        self.assertEqual(comprobante.mails_enviados, 1)
        
        mail = MailEnviadoComprobante(comprobante=comprobante, email="person@pirra.coop", fecha_envio=date.today(),
            estado="Ok", texto="")
        mail.save()
        self.assertEqual(comprobante.mails_enviados, 2)
