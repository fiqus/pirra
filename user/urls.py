from django.urls import path

from .views import create_user, create_company

urlpatterns = [
    path("create-user", create_user, name="create_user"),
    path("create-company", create_company, name="create_company")
]
