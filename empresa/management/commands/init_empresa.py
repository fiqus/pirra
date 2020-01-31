from django.core.management.base import BaseCommand

from empresa.models import Empresa


class Command(BaseCommand):
    help = 'Create empresa'

    def add_arguments(self, parser):
        parser.add_argument('nro_doc', type=str, help="CUIT or DNI number")
        parser.add_argument('nombre', type=str, help="Short name, not business name")

    def handle(self, *args, **options):
        empresa = Empresa(nro_doc=options['nro_doc'], nombre=options['nombre'])
        empresa.save()
