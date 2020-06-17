import csv
import shutil
import os

from jinja2 import Environment, FileSystemLoader

""" traer grupos y formatear para el template """
with open("./grupos.csv", "r") as grupos_csv:
    csv_reader = csv.reader(grupos_csv)
    groups = []

    for i, name in enumerate(csv_reader, start=1):
        groups.append({
            "name": name[0],
            "container_number": i
        })

file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)

""" genera docker-compose.yml """
template_yml = env.get_template("template.yml")
template_yml.stream(groups=groups).dump("./outputs/docker-compose.yml")

""" genera nginx.conf """
template_conf = env.get_template("template.conf")
template_conf.stream(groups=groups).dump("./outputs/nginx.conf")

""" mover al root (si existe lo reemplaza) """
src = "./outputs/"
dst = "./../"
docker_filename = "docker-compose.yml"
nginx_filename = "nginx.conf"
shutil.move(os.path.join(src, docker_filename), os.path.join(dst, docker_filename))
shutil.move(os.path.join(src, nginx_filename), os.path.join(dst, nginx_filename))
