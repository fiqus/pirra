from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.views.generic import DetailView

from afip.models import Unidad
from comprobante.models import Comprobante


class ComprobantePreview(DetailView):
    model = Comprobante

    def get_context_data(self, **kwargs):
        context = super(ComprobantePreview, self).get_context_data(**kwargs)
        if 'pk' in self.kwargs:
            comprobante = Comprobante.objects.get(pk=self.kwargs['pk'])
            obj = comprobante.get_data_para_imprimir()
            context['object'] = obj
            context['comprobante'] = comprobante

            importe_descuento = self.get_importe_descuento(comprobante)
            context['importe_neto_gravado'] = Comprobante.formatNumericFieldToFloat(comprobante, comprobante.importe_neto_gravado)
            context['importe_no_gravado'] = Comprobante.formatNumericFieldToFloat(comprobante, comprobante.importe_no_gravado)
            context['importe_exento'] = Comprobante.formatNumericFieldToFloat(comprobante, comprobante.importe_exento)
            context['importe_descuento'] = Comprobante.formatNumericFieldToFloat(comprobante, importe_descuento)

            tributos = comprobante.tributocomprobante_set.aggregate(
                total_tributos=Sum(F('base_imponible') * F('alicuota') / 100))
            total_tributos = tributos.get('total_tributos') if tributos.get('total_tributos') else 0

            if not comprobante.es_comprobante_b():
                subtotal = comprobante.importe_neto + comprobante.importe_dto_neto
            else:
                subtotal = comprobante.importe_total + importe_descuento - total_tributos
            context['subtotal'] = subtotal

        return context

    @staticmethod
    def get_importe_descuento(comprobante):
        importe_descuento = 0
        if comprobante.descuento and comprobante.descuento > 0:
            descuentos = comprobante.detallecomprobante_set.filter(unidad__id_afip=Unidad.BONIFICACION_ID_AFIP)
            for descuento in descuentos:
                if comprobante.muestra_subtotales():
                    importe_descuento += descuento.importe_neto
                else:
                    importe_descuento += descuento.precio_total
        return (importe_descuento * -1) if comprobante.descuento else 0


comprobante_preview = login_required(ComprobantePreview.as_view())
