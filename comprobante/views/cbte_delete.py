import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.edit import DeleteView

from comprobante.models import Comprobante

logger = logging.getLogger(__name__)

class ComprobanteDelete(DeleteView):
    model = Comprobante
    success_url = reverse_lazy('comprobante.list')

    @method_decorator(permission_required("comprobante.delete_comprobante", raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(ComprobanteDelete, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.cae:
            self.object.delete()

            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.error(request, " El comprobante ya fue autorizado y no puede ser eliminado.")
            return HttpResponseRedirect(reverse_lazy('comprobante.list'))


comprobante_delete = login_required(ComprobanteDelete.as_view())
