import csv
import shutil
import os

from jinja2 import Environment, FileSystemLoader

# get groups and format for template
with open("./all_groups.csv", "r") as grupos_csv:
    csv_reader = csv.reader(grupos_csv)
    groups = []

    for i, data in enumerate(csv_reader, start=1):
        group_name = data[0]
        env_var_name = ("% s_db_password"% group_name).upper()
        groups.append({
            "name": group_name,
            "password": data[1],
            "env_var_name": env_var_name,
            "container_number": i
        })

file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)

def create_file(templete_name, file_name):
    templete = env.get_template(templete_name)
    templete.stream(groups=groups).dump(file_name)

create_file("docker_compose_template.yml", "./outputs/docker-compose.yml")
create_file("nginx_template.conf", "./outputs/nginx.conf")
create_file("env_templete.j2", "./outputs/.env")

# move to root (if it exists replaces it)
src = "./outputs/"
dst = "./../"
docker_filename = "docker-compose.yml"
nginx_filename = "nginx.conf"
env_filename = ".env"
shutil.move(os.path.join(src, docker_filename), os.path.join(dst, docker_filename))
shutil.move(os.path.join(src, nginx_filename), os.path.join(dst, nginx_filename))
shutil.move(os.path.join(src, env_filename), os.path.join(dst, env_filename))
