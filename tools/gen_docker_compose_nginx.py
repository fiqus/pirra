import csv
import shutil
import os

from jinja2 import Environment, FileSystemLoader

# get groups and format for template
with open("./grupos.csv", "r") as grupos_csv:
    csv_reader = csv.reader(grupos_csv)
    groups = []

    for i, data in enumerate(csv_reader, start=1):
        groups.append({
            "name": data[0],
            "password": data[1],
            "container_number": i
        })

file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)

# generate docker-compose.yml
template_yml = env.get_template("template.yml")
template_yml.stream(groups=groups).dump("./outputs/docker-compose.yml")

# generate nginx.conf
template_conf = env.get_template("template.conf")
template_conf.stream(groups=groups).dump("./outputs/nginx.conf")

# move to root (if it exists replaces it)
src = "./outputs/"
dst = "./../"
docker_filename = "docker-compose.yml"
nginx_filename = "nginx.conf"
shutil.move(os.path.join(src, docker_filename), os.path.join(dst, docker_filename))
shutil.move(os.path.join(src, nginx_filename), os.path.join(dst, nginx_filename))
