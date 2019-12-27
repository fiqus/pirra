from django.apps import AppConfig
from django.urls import path, include

from hooks import hook


class SampleHooksConfig(AppConfig):
    name = 'sample_hooks'

    def ready(self):
        hook.register('pirra.urlpatterns', lambda: path(r'sample_hooks/', include('sample_hooks.urls')))
        import sample_hooks.hooks
