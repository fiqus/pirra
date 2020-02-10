# coding=utf-8
import string

from django.db.models import Sum
from django.db.models.expressions import F
from reportlab.platypus.tables import TableStyle

from afip.models import Unidad
from comprobante.pdf.document.base import Base
from comprobante.pdf.document.elements import CenterRestrictImage, RestrictParagraph, RestrictTable, VSpace, \
    PageCounterParagraph
from comprobante.pdf.stylesheets.default import get_default_stylesheet, _baseFontNameB
import logging


styles = get_default_stylesheet()
logger = logging.getLogger(__name__)


class StringFormatter(string.Formatter):
    def __init__(self, data):
        self.data = data

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val = super(StringFormatter, self).get_field(field_name, args, self.data)
        except (KeyError, AttributeError):
            val = None, field_name
        return val

    def format_field(self, value, spec):
        # handle an invalid format
        if value is None:
            return '-'
        return super(StringFormatter, self).format_field(value, spec)


class Invoice(Base):
    def __init__(self, filename, pagesize, comprobante, es_impresion, *args, **kwargs):
        self.cbte = comprobante
        self.cbte_data = comprobante.get_data_para_imprimir().copy()
        formatter = StringFormatter(self.cbte_data)
        self.f = formatter.format

        self.cbte_detail = comprobante.detallecomprobante_set.exclude(
            unidad__id_afip=Unidad.BONIFICACION_ID_AFIP).order_by('pk').all()

        self.datail_all = comprobante.detallecomprobante_set.order_by('pk').all()

        subtotal = 0
        importe_descuento = 0
        self.subtotales = []
        for detail in self.cbte_detail:
            subtotal += detail.importe_neto if self.cbte.muestra_subtotales() else detail.precio_total
            self.subtotales.append(subtotal)
        if comprobante.descuento and comprobante.descuento > 0:
            descuentos = comprobante.detallecomprobante_set.filter(unidad__id_afip=Unidad.BONIFICACION_ID_AFIP)
            for descuento in descuentos:
                importe_descuento += descuento.importe_neto if self.cbte.muestra_subtotales() else descuento.precio_total

        importe_descuento = importe_descuento * -1 if comprobante.descuento else 0
        importe_neto_gravado = comprobante.importe_neto_gravado
        importe_no_gravado = comprobante.importe_no_gravado
        importe_exento = comprobante.importe_exento

        tributos = comprobante.tributocomprobante_set.aggregate(
            total_tributos=Sum(F('base_imponible') * F('alicuota') / 100))
        subtotal_sin_tributos = subtotal - (tributos.get('total_tributos') if tributos.get('total_tributos') else 0)

        extra_data = {"importe_descuento": importe_descuento,
                      "importe_neto_gravado": importe_neto_gravado, "importe_no_gravado": importe_no_gravado,
                      "importe_exento": importe_exento, "subtotal": subtotal,
                      "subtotal_sin_tributos": subtotal_sin_tributos}

        self.cbte_data.update(extra_data)

        super(Invoice, self).__init__(filename, pagesize, es_impresion, *args, **kwargs)

    def _format_moneda(self, ammount):
        symbol = self.cbte_data.get("moneda", {}).get("simbolo", "$")
        return symbol + "{0:,.2f}".format(ammount)

    def gen_header1(self):
        w = self.header_col_width
        h = self.usable_height

        items = []

        if self.cbte.empresa.logo:
            items = items + [
                VSpace(),
                CenterRestrictImage(self.cbte.empresa.logo.path, w, 50),
                VSpace(),
                RestrictParagraph(self.f("{empresa[nombre]}"),
                                  w, h, styles["header_company_name"]),
            ]
        else:
            items = items + [
                VSpace(),
                RestrictParagraph(self.f("{empresa[nombre]}"),
                                  w, h, styles["header_company_name_large"]),
                VSpace(18),
            ]

        items = items + [
            # if LOGO else styles[ "header_company_name_large"])
            VSpace(),
            RestrictParagraph(self.f("""
                <b>Domicilio:</b> {empresa[domicilio]}<br/>
                <b>Localidad:</b> {empresa[localidad]}<br/>
                <b>Email:</b> {empresa[email]}<br/>
                <b>Condicion frente al IVA:</b> {empresa[condicion_iva]}
                """), w, h, styles["header_normal"]),
            VSpace(),
        ]

        return items

    def gen_header2(self, copy_number):
        nro_prefix = "Nº "
        w = self.header_col_width
        h = self.usable_height
        if self.cbte.cae:
            if copy_number == 1:
                invoice_copy_number_desc = "Original"
            if copy_number == 2:
                invoice_copy_number_desc = "Duplicado"
            elif copy_number == 3:
                invoice_copy_number_desc = "Triplicado"

        ret = [
            VSpace(),
            RestrictParagraph(self.f("{tipo_cbte[nombre]}") if self.cbte.cae else "No válido como factura", w, h,
                              styles["header_big"]),
            VSpace(),
            RestrictParagraph(invoice_copy_number_desc if self.cbte.cae else "", w, h, styles["header_big"]),
            VSpace(),

            RestrictParagraph(self.f(nro_prefix + "{pp_numero}").format(nro_prefix, self.cbte_data), w, h,
                              styles["header_medium"]),
            VSpace(),
            RestrictParagraph(
                self.f("<b>Orden de Compra:</b> {}<br/>").format(self.cbte.orden_compra.nro)
                if self.cbte.orden_compra else "" +
                self.f("""
        <b>Fecha de emision:</b> {fecha_emision}<br/>
        <b>CUIT:</b> {empresa[nro_doc_formatted]}<br/>"""
        + self.gen_header_iibb() +
        """<b>Fecha de inicio actividad:</b> {empresa[fecha_serv_desde]}
        """), w, h, styles["header_normal"]),
            VSpace(),
        ]

        return ret

    def gen_header_letter(self):
        if self.cbte.cae:
            if self.cbte.es_comprobante_m():
                return [
                    RestrictParagraph(self.f("{tipo_cbte[letra]}"), 68, 50, styles["header_letter"]),
                    RestrictParagraph("La operación igual o mayor a un mil pesos ($ 1.000.-) está sujeta a retención", 68, 50, styles["header_letter_xxs"]),
                    RestrictParagraph(self.f("COD. {tipo_cbte[id_afip]:02d}"), 68, 50, styles["header_letter_xs"]),
                ]
            else:
                return [
                    RestrictParagraph(self.f("{tipo_cbte[letra]}"), 50, 50, styles["header_letter"]),
                    RestrictParagraph(self.f("COD. {tipo_cbte[id_afip]:02d}"), 50, 50, styles["header_letter_xs"]),
                ]
        else:
            return [
                RestrictParagraph("No válido como factura", 50, 50, styles["header_letter_xs"])
            ]

    def gen_header_row2(self):
        w = self.usable_width
        h = self.usable_height
        if self.cbte_data["tipo_cbte"]["letra"] == "E":
            return [
                VSpace(),
                RestrictParagraph(self.f("""
 <b>Sres:</b> {cliente[nombre]}
 <b>Domicilio:</b> {cliente[domicilio]}
 <b>Localidad:</b> {cliente[localidad]}
 <b>Cuit Pais:</b> {pais_destino[cuit]}""").replace(" ", "&nbsp;"), w, h, styles["header_small"]),
                VSpace(),

            ]
        if self.cbte_data["cliente"]['nro_doc'] == '0':
            return [
                VSpace(),
                RestrictParagraph("<b>Consumidor Final</b>", w, h, styles["header_small"]),
                VSpace(),
            ]

        return [
            VSpace(),
            RestrictParagraph(self.f("""
 <b>Sres:</b> {cliente[nombre]}
 <b>Domicilio:</b> {cliente[domicilio]}
 <b>Localidad:</b> {cliente[localidad]}
 <b>Telefono:</b> {cliente[telefono]}""").replace(" ", "&nbsp;"), w, h, styles["header_small"]),
            VSpace(),

        ]

    def gen_header_row3(self):
        w = self.usable_width
        h = self.usable_height
        if self.cbte_data["tipo_cbte"]["letra"] == "E":
            data = """
 <b>Divisa:</b> {moneda[nombre]}
 <b>Destino:</b> {pais_destino[nombre]}
"""
            if self.cbte_data.get("forma_pago", False):
                data = data + "<b>Forma de pago:</b>: {forma_pago}"

            if self.cbte_data.get("incoterms", False):
                data = data + "<b>Incoterms:</b>: {incoterms}"

            if self.cbte_data.get("cbte_asoc", False):
                data = data + "<b>Asociado a</b>: {cbte_asoc[tipo_cbte][nombre]} {cbte_asoc[tipo_cbte][letra]} {cbte_asoc[pp_numero]}"

            if self.cbte_data.get("fecha_pago", False):
                data = data + "<b>Fecha Pago</b>: {fecha_pago}"

            return [
                VSpace(),
                RestrictParagraph(self.f(data).replace(" ", "&nbsp;"), w, h, styles["header_small"]),
                VSpace(),
            ]
        if self.cbte_data["cliente"]['nro_doc'] == '0':
            data = ""
        else:
            data = "<b>{cliente[tipo_doc]}: </b> {cliente[nro_doc_formatted]} "

        data += """ <b>IVA: </b> {cliente[condicion_iva]}
 <b>Remito: </b> {remito_nro}
 <b>Vto. Pago: </b> {fecha_venc_pago}
 <b>Cond. Venta: </b> {condicion_venta}"""
        return [
            VSpace(),
            RestrictParagraph(self.f(data).replace(" ", "&nbsp;"), w, h, styles["header_small"]),
            VSpace(),
        ]

    def gen_footer_legend(self):
        w = self.usable_width
        h = self.usable_height

        s = self
        def get_data():
            return "Página {} de {}".format(s.page_number, len(s.paged_detail_items))

        return [
            RestrictParagraph(
                "Esta factura electrónica fue confeccionada con el sistema de Facturación Electrónica "
                "Pirra. "
                "La información contenida en éste documento es privilegiada y confidencial, para uso exclusivo "
                "de los destinatarios de la misma y/o de quienes hayan sido autorizados específicamente para leerla.",
                w, h, styles['legend_xs']),
            VSpace(),
            PageCounterParagraph("Página 1 de 1", get_data, w, h, styles['legend_xs'])
        ]

    gen_footer_legend_last_page = gen_footer_legend

    def gen_footer_col2_last_page(self):
        w = self.usable_width / 2
        h = self.usable_height

        data = []
        descuento = float(self.cbte_data.get("descuento", 0)) if self.cbte_data.get("descuento", 0) else 0
        if self.cbte.muestra_subtotales() or descuento > 0 or self.cbte.muestra_tributos():
            data.append(["Subtotal", self._format_moneda(self.cbte_data["subtotal"])])

        if descuento > 0:
            desc_title = "Descuento"
            desc_title += " {:.2f} %".format(float(self.cbte_data["descuento"]))
            data.append([desc_title, self._format_moneda(self.cbte_data["importe_descuento"])])

        if self.cbte.muestra_subtotales():
            data.append(["Neto Gravado", self._format_moneda(self.cbte_data["importe_neto_gravado"])])
            if self.cbte_data.get("importe_no_gravado", 0):
                data.append(["No Gravado", self._format_moneda(self.cbte_data["importe_no_gravado"])])
            if self.cbte_data.get("importe_exento", 0):
                data.append(["Exento", self._format_moneda(self.cbte_data["importe_exento"])])

            for alicuota in list(self.cbte.importes_ivas.values()):
                data.append(["{} {:.2f}".format(alicuota["nombre"], alicuota["porc"]),
                             self._format_moneda(alicuota["valor"])])

        if self.cbte.muestra_tributos():
            for tributo in self.cbte.tributocomprobante_set.all():
                data.append([tributo.detalle, self._format_moneda(tributo.total)])

        data.append(["Importe Total", self._format_moneda(float(self.cbte_data["importe_total"]))])

        tbl = RestrictTable(data, w, h, None, [w - 70, 70])
        tablestyle = TableStyle([('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                                 ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                                 ('TOPPADDING', (0, -1), (-1, -1), 8),
                                 ('TEXTCOLOR', (0, 0), (-1, -1), (.3, .3, .3)),
                                 ('FONTNAME', (0, -1), (-1, -1), _baseFontNameB),
                                 ('FONTSIZE', (0, 0), (-1, -1), 8)])

        tbl.setStyle(tablestyle)

        return [VSpace(),
                tbl,
                VSpace()]

    def gen_footer_col2(self):
        w = self.usable_width / 2
        h = self.usable_height

        s = self
        footer_totals_data = [["Subtotal", "000"]]

        def get_data():
            return [["Subtotal", s._format_moneda(s.subtotales[s.drawn_items - 1])]]

        tbl = RestrictTable(footer_totals_data, w, h, get_data, [w - 70, 70])
        tablestyle = TableStyle([('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                                 ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                                 ('TOPPADDING', (0, -1), (-1, -1), 8),
                                 ('TEXTCOLOR', (0, 0), (-1, -1), (.3, .3, .3)),
                                 ('FONTNAME', (0, -1), (-1, -1), _baseFontNameB),
                                 ('FONTSIZE', (0, 0), (-1, -1), 8)])

        tbl.setStyle(tablestyle)

        return [VSpace(),
                tbl,
                VSpace()]

    def gen_footer_col1_last_page(self):
        w = self.usable_width / 2
        h = self.usable_height

        if self.cbte.cae:
            return [
                VSpace(),
                RestrictParagraph(self.f("""
                    <b>CAE Nº:</b> {cae}<br/>
                    <b>Vto. CAE:</b> {fecha_vto_cae}<br/>
                    """), w, h, styles["header_normal"]),
                VSpace(),
                CenterRestrictImage(self.cbte.codigo_barras.path, w, 30, 8),
                RestrictParagraph(self.cbte.codigo_barras_nro, w, h, styles['header_small_center']),
                VSpace(),
            ]
        else:
            return [
                VSpace(),
                RestrictParagraph("""No válido como factura""", w, h, styles["header_big"]),
                VSpace(),
            ]

    def gen_footer_col1(self):
        return []

    def gen_detail_header(self):
        w = self.usable_width
        s = 50
        l = 65
        data = [
            RestrictParagraph("Cant.", s, 40, styles['detail_header_right']),
            RestrictParagraph("Unidad", s, 40, styles['detail_header_left']),
            RestrictParagraph("Descripción", w - (s * 5) - (l if self.cbte.discrimina_iva() else -s), 40,
                              styles['detail_header_left']),
            RestrictParagraph("Precio Unit.", s, 40, styles['detail_header_right']),
        ]
        if self.cbte.discrimina_iva():
            data += [
                RestrictParagraph("Subtotal", s, 40, styles['detail_header_right']),
                RestrictParagraph("IVA", l, 40, styles['detail_header_right']),
            ]
        data += [
            RestrictParagraph("Total", s, 40, styles['detail_header_right']),
        ]
        return data

    def gen_detail_items(self):
        w = self.usable_width
        s = 50
        l = 65
        items = []

        for det in self.cbte_detail:

            it = [
                RestrictParagraph("{:.2f}".format(det.cant), s, self.detail_height, styles['detail_right']),
                RestrictParagraph(str(det.unidad), s, self.detail_height, styles['detail_left']),
                RestrictParagraph(det.detalle, w - (s * 5) - (l if self.cbte.discrimina_iva() else -s),
                                  self.detail_height, styles['detail_left']),
                RestrictParagraph(self._format_moneda(
                    det.precio_unit if self.cbte.discrimina_iva()
                    else det.precio_unitario_con_iva),
                    s, self.detail_height, styles['detail_right']),
            ]
            if self.cbte.discrimina_iva():
                it += [
                    RestrictParagraph(self._format_moneda(det.importe_neto), s, self.detail_height, styles['detail_right']),
                    RestrictParagraph(str(det.alicuota_iva), l, self.detail_height, styles['detail_right']),
                ]
            it += [
                RestrictParagraph(self._format_moneda(det.precio_total), s, self.detail_height, styles['detail_right']),
            ]
            items.append(it)
        return items

    def gen_footer_observaciones(self):
        w = self.usable_width
        h = self.usable_height

        if self.cbte.observaciones:
            return [
                VSpace(),
                RestrictParagraph("<b>Observaciones: </b> " + self.cbte.observaciones, w, h,
                                  styles['header_small']),
                VSpace()
            ]
        else:
            return []

    def gen_header_iibb(self):
        if self.cbte.empresa.es_iibb_otra:
            return """<b>IIBB:</b> {empresa[nro_iibb]}<br/>"""
        else:
            return """<b>IIBB:</b> {empresa[condicion_iibb]}""" + (""" - {empresa[nro_iibb]}<br/>"""
                              if self.cbte.empresa.nro_iibb else """<br/>""")
