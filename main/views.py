# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from empresa.models import Empresa, PuntoDeVenta
from help.models import LatestNews
from main.dashboard import get_dashboard_data
from user.models import ProxiUser


@login_required
def index_customer(request):
    proxi_user = ProxiUser.objects.get(user=request.user)
    empresa = proxi_user.company

    ctx = {
        # 'ptos_vta': PuntoDeVenta.objects.filter(activo=True).count(),
        'ptos_vta': PuntoDeVenta.objects.filter(empresa=empresa, activo=True).count(),
        'empresa_tipos_cbte': empresa.tipos_cbte.count(),
        'empresa_concepto': 1 if empresa.concepto else 0,
        'dashboard_data': get_dashboard_data(),
    }
    return render(request, 'index_customer.html', ctx)