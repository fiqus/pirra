from django.urls import path

from sample_hooks.views import test_view

urlpatterns = [
    path('hook_view', test_view, name='sample_hooks.test_view'),
]