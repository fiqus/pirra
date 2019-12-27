from django.contrib.auth.models import User
from django.db import models

from afip.models import CondicionIva, CondicionIIBB, TipoDoc, Concepto, TipoComprobante, AlicuotaIva, Unidad, \
    ResolucionGeneral, Opcional
from django.core.exceptions import ValidationError


def cuit_format(cuit):
    cuit = str(cuit)
    return '%s-%s-%s' % (cuit[:2], cuit[2:-1], cuit[-1])


class Empresa(models.Model):
    nombre = models.CharField(max_length=256)
    nro_doc = models.CharField(max_length=128)
    email = models.EmailField(null=True, blank=True)
    domicilio = models.CharField(max_length=256, null=True, blank=True)
    localidad = models.CharField(max_length=256, null=True, blank=True)
    cod_postal = models.CharField(max_length=256, null=True, blank=True)
    condicion_iva = models.ForeignKey(CondicionIva, null=True, blank=True, on_delete=models.CASCADE)
    condicion_iibb = models.ForeignKey(CondicionIIBB, null=True, on_delete=models.CASCADE)
    nro_iibb = models.CharField(max_length=128, null=True, blank=True)
    concepto = models.ForeignKey(Concepto, null=True, blank=True, on_delete=models.CASCADE)
    tipos_cbte = models.ManyToManyField(TipoComprobante)
    resoluciones_generales = models.ManyToManyField(ResolucionGeneral, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    fecha_serv_desde = models.DateField(null=True, blank=True)
    fecha_serv_hasta = models.DateField(null=True, blank=True)

    logo = models.ImageField(null=True, blank=True, upload_to="logos")
    mandar_copia_comprobante = models.BooleanField(default=True)
    imprimir_comp_triplicado = models.BooleanField(default=False)

    utiliza_edi = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

    @property
    def nro_doc_formatted(self):
        return cuit_format(self.nro_doc)

    @property
    def tieneTiposCbte(self):
        return self.tipos_cbte.count() > 0

    @property
    def es_iibb_exenta(self):
        return (self.condicion_iibb.pk == CondicionIIBB.EXENTO) if self.condicion_iibb else False

    @property
    def es_iibb_otra(self):
        return (self.condicion_iibb.pk == CondicionIIBB.OTRA) if self.condicion_iibb else False

    def tiene_opcionales(self):
        return self.resoluciones_generales is not None and self.resoluciones_generales.count() > 0

    def get_opcionales(self):
        return Opcional.objects.filter(resolucion_general__in=self.resoluciones_generales.all())

    def get_opcionales_grouped(self):
        opcionales = {}
        if self.tiene_opcionales():
            for rg in self.resoluciones_generales.all():
                key = "{}-{}".format(rg.nombre, rg.numero)
                opcionales[key] = rg.opcional_set.all()
            return opcionales
        else:
            return opcionales

    def get_resoluciones_generales_as_title(self):
        if self.tiene_opcionales():
            rgs = ""
            for rg in self.resoluciones_generales.all():
                if rgs:
                    rgs += " / "
                rgs += "RG {}: {}".format(rg.numero, rg.nombre)
            return rgs
        else:
            return set()

    def get_resoluciones_generales(self):
        if self.tiene_opcionales():
            return self.resoluciones_generales.all()
        else:
            return set()


class BajaLogicaClass(models.Model):
    activo = models.BooleanField(default=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    usuario_baja = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def hard_delete(self):
        super(BajaLogicaClass, self).deleted()


class PuntoDeVenta(BajaLogicaClass):
    id_afip = models.IntegerField(verbose_name='Nro Punto de Venta')
    nombre = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre


class Cliente(BajaLogicaClass):
    tipo_doc = models.ForeignKey(TipoDoc, on_delete=models.CASCADE)
    nro_doc = models.CharField(max_length=128)
    nombre = models.CharField(max_length=256)
    condicion_iva = models.ForeignKey(CondicionIva, on_delete=models.CASCADE)
    domicilio = models.CharField(max_length=256)
    localidad = models.CharField(max_length=256)
    telefono = models.CharField(max_length=256, null=True, blank=True)
    cod_postal = models.CharField(max_length=256, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    editable = models.BooleanField(default=True)
    agente_edi = models.BooleanField(default=False)

    def clean(self):
        tipo_doc_value = self.tipo_doc.nombre.lower()
        if tipo_doc_value in ['cuit', 'cuil', 'dni']: #validar estos campos
            cts = Cliente.objects.filter(nro_doc=self.nro_doc, tipo_doc=self.tipo_doc)
            if self.pk is not None:
                cts = cts.exclude(pk=self.pk)
            if cts.exists():
                if cts.first().activo:
                    raise ValidationError('Ya existe un cliente con el mismo tipo y nro de documento.')
                else:
                    raise ValidationError("Existe un cliente inactivo con el mismo tipo y nro de documento. "
                                          "Por favor busquelo en el listado de clientes y activelo para evitar"
                                          " tener registros duplicados.")

    @property
    def nro_doc_formatted(self):
        if self.tipo_doc.id_afip in (TipoDoc.CUIT, TipoDoc.CUIL):
            return cuit_format(self.nro_doc)
        return self.nro_doc

    def __str__(self):
        return "{0} - {1}".format(self.nombre, self.nro_doc_formatted)


class Producto(BajaLogicaClass):
    codigo = models.CharField(max_length=128, blank=True)
    nombre = models.CharField(max_length=256)
    precio_unit = models.DecimalField(max_digits=19, decimal_places=4)
    alicuota_iva = models.ForeignKey(AlicuotaIva, null=True, blank=True, on_delete=models.CASCADE)
    unidad = models.ForeignKey(Unidad, null=True, on_delete=models.CASCADE)
    ingresa_precio_final = models.BooleanField(default=False)

    codigo_barras_nro = models.DecimalField(max_digits=13, decimal_places=0, null=True, blank=True)
    # Especifica si el producto fue dado de alta automaticamente por EDI
    alta_edi = models.BooleanField(default=False)

    @property
    def nombre_completo(self):
        if self.codigo:
            return "{} - {}".format(self.codigo, self.nombre)
        else:
            return self.nombre

    @property
    def precio_final(self):
        return self.precio_unit * (1 + self.alicuota_iva.porc / 100)

    def __str__(self):
        return self.nombre_completo


# class PlanEmpresa(models.Model):
#     empresa= models.ForeignKey(Empresa)
#     plan = models.ForeignKey(Plan)
#     fecha_desde =
#     fecha_hasta =
