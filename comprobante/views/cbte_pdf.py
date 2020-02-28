import io
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from comprobante.models import Comprobante
from comprobante.pdf.document.invoice import Invoice
from comprobante.views.cbte_autorizar import genera_codigo_barra


def gen_pdf_file(pdf, comprobante, es_impresion):
    Invoice(pdf, A4, comprobante, es_impresion).gen_pdf(es_impresion)
    pdf.seek(0)


def fetch_resources(uri, _):
    import os
    from django.conf import settings

    """
    Callback to allow xhtml2pdf/reportlab to retrieve Images,Stylesheets, etc.
    `uri` is the href attribute from the html link element.
    `rel` gives a relative path, but it's not used here.

    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT,
                            uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT,
                            uri.replace(settings.STATIC_URL, ""))
    else:
        path = os.path.join(settings.STATIC_ROOT,
                            uri.replace(settings.STATIC_URL, ""))

        if not os.path.isfile(path):
            path = os.path.join(settings.MEDIA_ROOT,
                                uri.replace(settings.MEDIA_URL, ""))

            if not os.path.isfile(path):
                raise Exception('media urls must start with %s or %s' % (settings.MEDIA_ROOT, settings.STATIC_ROOT))

    return path


@login_required
def comprobante_to_pdf(_, pk):
    comprobante = Comprobante.objects.get(pk=pk)

    # Chequeo de existencia de archivo
    filename = os.path.join(settings.MEDIA_ROOT, comprobante.codigo_barras.name)
    if not os.path.isfile(filename):
        genera_codigo_barra(comprobante)
    result = io.BytesIO()
    try:
        gen_pdf_file(result, comprobante, True)
        res = HttpResponse(
            result.getvalue(),
            content_type='application/pdf', )
    finally:
        result.close()

    fname = "comprobante-{}.pdf".format(comprobante.pp_numero) if comprobante.nro else "comprobante.pdf"
    res["content-disposition"] = "attachment; filename={}".format(fname)
    return res
