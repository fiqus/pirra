from django.core.management.base import BaseCommand

from empresa.models import Empresa


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('nro_doc', type=str)
        parser.add_argument('nombre', type=str)

    def handle(self, *args, **options):
        empresa = Empresa(nro_doc=options['nro_doc'], nombre=options['nombre'])
        empresa.save()
