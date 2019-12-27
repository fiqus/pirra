import codecs

from django.contrib.auth.decorators import login_required, permission_required
from django.forms import Form, FileField
from django.shortcuts import render

from comprobante.csv_import import import_cbte_csv


class CbteImportForm(Form):
    file = FileField(label="Archivo")

    def save(self):
        StreamReader = codecs.getreader('utf-8')
        errors = import_cbte_csv(StreamReader(self.cleaned_data["file"]))
        if errors:
            for err in errors:
                self.add_error(None, err)


@login_required()
@permission_required('comprobante.add_comprobante', raise_exception=True)
def cbte_import(request):
    cuenta_exception = False

    if request.method == 'POST':
        form = CbteImportForm(request.POST, request.FILES)
    else:
        form = CbteImportForm()
    if form.is_valid():
        form.save()

        if not form.errors:
            return render(request, "comprobante/import_success.html")

    return render(request, "comprobante/import_form.html",
                  {"form": form, "cuenta_exception": cuenta_exception})
