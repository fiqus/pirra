from ckeditor.fields import RichTextField
from django.db import models


# Create your models here.
class CondicionIva(models.Model):
    # pks constantes
    RESP_INSCRIPTO = 1
    EXENTO = 2
    RESP_NO_INSCRIPTO = 3
    NO_RESP = 4
    CONS_FINAL = 5
    RESP_MONOTRIBUTO = 6
    CLI_EXTERIOR = 9

    id_afip = models.IntegerField()
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["id_afip"]


class CondicionIIBB(models.Model):
    # pks
    REG_SIMPLIFICADO = 1
    EXENTO = 2
    OTRA = 3

    id_afip = models.IntegerField()
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class TipoDoc(models.Model):
    # id_afips constantes
    CUIT = 80
    CUIL = 86
    OTRO = 99

    id_afip = models.IntegerField()
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class AlicuotaIva(models.Model):
    # id_afips constantes
    NO_GRAVADO = 1
    EXENTO = 2
    IVA_0 = 3
    IVA_0_PK = 1
    IVA_10_5_PK = 2
    IVA_21 = 5
    IVA_21_PK = 3
    IVA_27_PK = 4
    IVA_5 = 8
    IVA_5_PK = 5
    IVA_2_5_PK = 6
    NO_GRAVADO_PK = 7
    EXENTO_PK = 8

    id_afip = models.IntegerField()
    nombre = models.CharField(max_length=256)
    porc = models.DecimalField(max_digits=19, decimal_places=4)

    def __str__(self):
        return self.nombre + " {0:.2f}".format(self.porc) + "%"

    def porcentaje(self):
        return "{0:.2f}".format(self.porc) + "%"

    @property
    def id_tipo_cbtes(self):
        return ",".join([str(i.tipo_comp.id) for i in self.tipocomprobantealicuotaiva_set.all()])


class TipoComprobanteAlicuotaIva(models.Model):
    alicuota_iva = models.ForeignKey("AlicuotaIva", on_delete=models.CASCADE)
    tipo_comp = models.ForeignKey("TipoComprobante", on_delete=models.CASCADE)

    orden = models.IntegerField()

    def __str__(self):
        return str(self.alicuota_iva)


class TipoComprobante(models.Model):
    # id_afips constantes
    FACTURA_A = 1
    ND_A = 2
    NC_A = 3
    RECIBO_A = 4
    FACTURA_A_PK = 1
    ND_A_PK = 2
    NC_A_PK = 3

    FACTURA_B = 6
    ND_B = 7
    NC_B = 8
    RECIBO_B = 9
    FACTURA_B_PK = 5
    ND_B_PK = 6
    NC_B_PK = 7
    RECIBO_B_PK = 8

    FACTURA_C = 11
    ND_C = 12
    NC_C = 13
    RECIBO_C = 15
    FACTURA_C_PK = 12
    ND_C_PK = 13
    NC_C_PK = 14
    RECIBO_C_PK = 15

    FACTURA_E = 19
    ND_E = 20
    NC_E = 21
    FACTURA_E_PK = 9
    ND_E_PK = 10
    NC_E_PK = 11

    FACTURA_M = 51
    ND_M = 52
    NC_M = 53
    RECIBO_M = 54
    FACTURA_M_PK = 16
    ND_M_PK = 17
    NC_M_PK = 18
    RECIBO_M_PK = 19

    id_afip = models.IntegerField()
    nombre = models.CharField(max_length=256)
    letra = models.CharField(max_length=1)

    def __str__(self):
        return "{} {}".format(self.nombre, self.letra)


class TipoExportacion(models.Model):
    id_afip = models.IntegerField()
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class Moneda(models.Model):
    id_afip = models.CharField(max_length=10)
    nombre = models.CharField(max_length=256)
    simbolo = models.CharField(max_length=3)

    def __str__(self):
        return "{} - {}".format(self.simbolo, self.nombre)


class Idioma(models.Model):
    id_afip = models.IntegerField()
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class Unidad(models.Model):
    BONIFICACION_ID_AFIP = 99
    KILOGRAMO_ID_AFIP = 1
    UNIDADES_ID_AFIP = 7

    id_afip = models.IntegerField()
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class Incoterms(models.Model):
    id_afip = models.CharField(max_length=10)
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class PaisDestino(models.Model):
    id_afip = models.CharField(max_length=10)
    nombre = models.CharField(max_length=256)
    cuit = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class CondicionVenta(models.Model):
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class Concepto(models.Model):
    # id_afips constantes
    PRODUCTOS = 1
    SERVICIOS = 2
    PRODUCTOS_SERVICIOS = 3

    id_afip = models.IntegerField()
    ws_afip = models.CharField(max_length=20, null=True)
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class Padron(models.Model):
    cuit = models.CharField(max_length=11, primary_key=True)
    denominacion = models.CharField(max_length=30)
    imp_ganancias = models.CharField(max_length=2)
    imp_iva = models.CharField(max_length=2)
    monotributo = models.CharField(max_length=2)
    integrante_soc = models.CharField(max_length=1)
    empleador = models.CharField(max_length=1)
    actividad_monotributo = models.CharField(max_length=2)

    def __str__(self):
        return "{} - {}".format(self.cuit, self.denominacion)

    def get_condicion_iva(self):
        if self.imp_iva == "AC":
            return CondicionIva.RESP_INSCRIPTO
        elif self.imp_iva == "EX":
            return CondicionIva.EXENTO
        elif self.imp_iva == "NI" and self.monotributo != "NI":
            return CondicionIva.RESP_MONOTRIBUTO
        else:
            return None


class Tributo(models.Model):
    # id_afips constantes
    NACIONALES = 1
    PROVINCIALES = 2
    MUNICIPALES = 3
    INTERNOS = 4
    OTRO = 99
    id_afip = models.CharField(max_length=10)
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class ResolucionGeneral(models.Model):
    numero = models.CharField(max_length=256, null=True, blank=True)
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return "RG {} {}".format(self.numero, self.nombre)


class Opcional(models.Model):
    id_afip = models.CharField(max_length=10)
    resolucion_general = models.ForeignKey(ResolucionGeneral, on_delete=models.CASCADE)
    campo = models.CharField(max_length=256)

    @property
    def tiene_opciones(self):
        return self.opcionopcional_set.count() > 0

    def __str__(self):
        return "{} - {}".format(self.resolucion_general, self.campo)


class OpcionOpcional(models.Model):
    opcional = models.ForeignKey('Opcional', on_delete=models.CASCADE)
    valor = models.CharField(max_length=256)
    descripcion = models.CharField(max_length=256)

    def __str__(self):
        return "{} - {} - {}".format(self.opcional.resolucion_general.numero, self.opcional.campo, self.descripcion)


class ErrorCustomAfip():
    CONECTIVIDAD = 'conectividad'

    errores = [
        {
            "codigo": "600",
            "descripcion": "<p>AFIP a&uacute;n no valido la relaci&oacute;n entre su empresa y Pirra.</p> <p>Si todav&iacute;a no inici&oacute; los tramites en la AFIP para vincular a Pirra como su facturador, siga los pasos indicados en los instructivos de vinculaci&oacute;n de Pirra. Caso contrario, espere 24 hs h&aacute;biles para poder autorizar.</p>",
            "regex": "CUIT"
        },
        {
            "codigo": "600",
            "descripcion": "<p>El servicio de AFIP no est&aacute;&nbsp;disponible en estos momentos, vuelva a intentarlo en unos instantes.</p>",
            "regex": "VerificacionDeHash"
        },
        {
            "codigo": "602",
            "descripcion": "<p>Hay datos err&oacute;neos en el comprobante generado.</p>"
        },
        {
            "codigo": "10016",
            "descripcion": "<p>Error en la fecha de emisi&oacute;n del comprobante. Recuerde que la misma debe estar comprendida en el rango N-10 y N+10 siendo N la fecha de hoy.</p>"
        },
        {
            "codigo": "10015",
            "descripcion": "<p>El monto total del comprobante generado supera el m&aacute;ximo permitido para el tipo de comprobante seleccionado. Recuerde que para Facturas B o C emitadas a un Consumidor Final el monto no debe ser mayor a $1000.</p>",
            "regex": "mayor o igual a $1000"
        },
        {
            "codigo": "10015",
            "descripcion": "<p>El n&uacute;mero de documento del cliente seleccionado no es v&aacute;lido.</p>",
            "regex": "menor a $1000"
        },
        {
            "codigo": "10015",
            "descripcion": "<p>El n&uacute;mero de documento del cliente seleccionado no es v&aacute;lido.</p>",
            "regex": "titular no se encuentra registrado"
        },
        {
            "codigo": "10015",
            "descripcion": "<p>El n&uacute;mero de documento del cliente seleccionado no es v&aacute;lido.</p>",
            "regex": "DocNro es invalido"
        },
        {
            "codigo": "10015",
            "descripcion": "<p>Verifique los datos de su cliente. El n&uacute;mero de documento del mismo no se encuentra registrado en los padrones de AFIP. </p>",
            "regex": "no se encuentra registrado en los padrones de AFIP"
        },
        {
            "codigo": "10013",
            "descripcion": "<p>Debe seleccionar un cliente correcto para el tipo de comprobante a emitir. Por ejemplo, si est&aacute; emitiendo una Factura A <strong>NO</strong> debe seleccionar un cliente que sea Consumidor Final.</p>"
        },
        {
            "codigo": "1000",
            "descripcion": "<p>AFIP a&uacute;n no valido la relaci&oacute;n entre su empresa y Pirra.</p> <p>Si todav&iacute;a no inici&oacute; los tramites en la AFIP para vincular a Pirra como su facturador, siga los pasos indicados en los instructivos de vinculaci&oacute;n de Pirra. Caso contrario, espere 24 hs h&aacute;biles para poder autorizar.</p>"
        },
        {
            "codigo": "10063",
            "descripcion": "<p>Se est&aacute; emitiendo un factura A a un CUIT que no est&aacute; registrado como Responsable Inscripto.</p>"
        },
        {
            "codigo": "10036",
            "descripcion": "<p>Se especific&oacute; una fecha de vencimiento de pago anterior a la fecha de emisi&oacute;n del comprobante.</p>"
        },
        {
            "codigo": "10000",
            "descripcion": "<p>El usuario no est&aacute; autorizado para emitir comprobantes. Existen inconvenientes con su domicilio fiscal.</p>"
        },
        {
            "codigo": "10065",
            "descripcion": "<p>El importe total del comprobante no puede ser menor a cero (0).</p>"
        },
        {
            "codigo": "10045",
            "descripcion": "<p>El importe neto (importe neto gravado) del comprobante no puede ser menor a cero (0).</p>"
        },
        {
            "codigo": "10047",
            "descripcion": "<p>El IVA no puede ser menor a cero (0).</p>"
        },
        {
            "codigo": "10021",
            "descripcion": "<p>El importe del campo IVA no puede ser menor a cero (0).</p>"
        },
        {
            "codigo": "10096",
            "descripcion": "<p>El usuario no est&aacute; autorizado para emitir comprobantes. Existen inconvenientes con el punto de venta informado.</p>"
        },
        {
            "codigo": "10004",
            "descripcion": "<p>No se ha especificado un punto de venta.</p>"
        },
        {
            "codigo": "500",
            "descripcion": "<p>El servicio de AFIP no est&aacute;&nbsp;disponible en estos momentos, vuelva a intentarlo en unos instantes.</p>"
        },
        {
            "codigo": "501",
            "descripcion": "<p>El servicio de AFIP no est&aacute;&nbsp;disponible en estos momentos, vuelva a intentarlo en unos instantes.</p>"
        },
        {
            "codigo": "conectividad",
            "descripcion": "<p>El servicio de AFIP no est&aacute;&nbsp;disponible en estos momentos, vuelva a intentarlo en unos instantes.</p>",
            "regex": "AttributeError:makefile:Tag not Found:Body:socket.error:Errno 104:ExpatError:Not well formed token:not well-formed (invalid token):BadStatusLine:ResponseNotReady:SSLError:timed out:Service Unavailable:ORA"
        },
        {
            "codigo": "1500",
            "descripcion": "<p>La fecha del comprobante debe estar incluida en el per&iacute;odo N-5 y N+5 siendo N la fecha de emisi&oacute;n del mismo.</p>"
        }
    ]

    def get_error(self, error_code):
        return [error for error in self.errores if error["codigo"] == error_code]
