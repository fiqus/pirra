from django.core.management import BaseCommand

from empresa.models import Empresa


class Command(BaseCommand):
    def handle(self, *args, **options):
        empresa = Empresa(nombre="test", nro_doc="33712225659")
        empresa.save()