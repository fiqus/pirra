from django.contrib.auth.models import User
from django.db import models

from empresa.models import Empresa


class ProxiUser(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    company = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.CASCADE)
    dni = models.CharField(max_length=100, unique=True, null=True, blank=True)
