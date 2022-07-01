from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from hooks import hook
from main.views import index_customer

urlpatterns = [
    path('', index_customer, name="index"),
    path('accounts/', include('django.contrib.auth.urls')),

    path('comprobantes/', include('comprobante.urls')),
    path('empresa/', include('empresa.urls')),
    path(r'ayuda/', include('help.urls')),
    path(r'afip/', include('afip.urls')),
    path('admin/', admin.site.urls),
    path('robots.txt', TemplateView.as_view(template_name='robots/client.txt', content_type='text/plain')),
    path('user/', include('user.urls'))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += hook('pirra.urlpatterns')
