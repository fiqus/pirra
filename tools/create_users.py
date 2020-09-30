import subprocess
import csv
import os

with open("./first_batch.csv.csv", "r") as grupos_csv:
    csv_reader = csv.reader(grupos_csv)
    admin_user = os.getenv("ADMIN_USER")
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_pass = os.getenv("ADMIN_PASS")

    for i, data in enumerate(csv_reader, start=1):
        group_name = data[0]
        group_cuit = data[1]
        container_name = "pirra_" + str(i)

        p1 = subprocess.Popen(["docker-compose", "exec", container_name, "python3", "manage.py", "migrate"])
        p1.wait()

        # create a user for the teacher in each group
        p2 = subprocess.Popen(
            [
                "docker-compose", "exec", container_name, "python3", "manage.py", "shell", "-c", 
                "from django.contrib.auth import get_user_model; User = get_user_model(); \
                    User.objects.create_superuser('" + admin_user + "', '" + admin_email + "', '" + admin_pass + "')"
            ]
        )
        p2.wait()

        # create a user for the group
        create_group_user = "from django.contrib.auth import get_user_model;\
            User = get_user_model(); User.objects.create_superuser('" + group_name + "', '', '" + group_cuit + "')"

        print("CREATING USER " + group_name + " TO GROUP " + group_name + " CREATED!")

        p3 = subprocess.Popen(["docker-compose", "exec", container_name, "python3", "manage.py", "shell", "-c", create_group_user])
        p3.wait()

        # create company
        p4 = subprocess.Popen(["docker-compose", "exec", container_name, "python3", "manage.py", "init_empresa", group_cuit, group_name])
        p4.wait()

        print("GROUP " + group_name + " CREATED!")