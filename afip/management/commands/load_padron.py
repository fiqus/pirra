import csv
import os
import urllib.request
import zipfile
from tempfile import TemporaryDirectory, TemporaryFile
from socket import error as sock_error

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.core.management import BaseCommand
from django.db import transaction, connection

from afip.models import Padron


def download(url, dest):
    req = urllib.request.urlopen(url)
    print(url)
    CHUNK = 16 * 1024
    while True:
        chunk = req.read(CHUNK)
        if not chunk:
            break
        dest.write(chunk)


def load_padron(filename, limit=0):
    print("loading", filename)
    with open(filename, 'r', encoding="ISO-8859-1") as f, \
            NamedTemporaryFile(mode='w+', suffix='.csv', encoding='utf-8', delete=True) as csvf:
        csvwriter = csv.writer(csvf, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        for i, line in enumerate(f):
            csvwriter.writerow(
                [line[0:11], line[11:41], line[41:43],
                 line[43:45], line[45:47], line[47], line[48], line[49:51]])

            if limit and i >= limit - 1:
                break

        csvf.seek(0)
        os.chmod(csvf.name, 0o666)

        with transaction.atomic():
            Padron.objects.all().delete()
            cursor = connection.cursor()
            cursor.execute("COPY afip_padron (cuit, denominacion, imp_ganancias, imp_iva, monotributo, "
                           "integrante_soc, empleador, actividad_monotributo) "
                           "FROM %s DELIMITER AS ',' QUOTE '|' CSV;", [csvf.name])

        csvf.close()


class Command(BaseCommand):
    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Number of lines to load'
        )

        parser.add_argument(
            '--file',
            type=str,
            help='load from this file instead of downloading'
        )

        parser.add_argument(
            '--retry',
            type=int,
            default=5,
            help='retry the download if it fails (N times)'
        )

    def handle(self, *args, **options):
        url = settings.PADRON_URL

        if options["file"]:
            load_padron(options["file"], options["limit"])
        else:
            with TemporaryFile() as f:
                ret = options["retry"]
                while ret:
                    try:
                        print("downloading", url)
                        download(url, f)
                    except sock_error as err:
                        print("connection error ({})".format(err.errno))
                        ret -= 1
                        print("download failed...")
                        if not ret:
                            raise
                        else:
                            print("retrying...")
                        continue
                    ret = 0
                path = TemporaryDirectory()
                print("extracting to", path.name)
                f.seek(0)
                z = zipfile.ZipFile(f)
                z.extractall(path.name)
                print("extracted")

                path_padron = os.path.join(path.name, "utlfile/padr")
                print("loading file {}".format(os.listdir(path_padron)[0]))
                load_padron(os.path.join(path_padron, os.listdir(path_padron)[0]), options["limit"])

        self.stdout.write(self.style.SUCCESS('Successfully load padron'))
