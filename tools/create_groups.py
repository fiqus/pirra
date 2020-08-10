import subprocess
import csv

# get groups and format for template
with open("./grupos.csv", "r") as grupos_csv:
    csv_reader = csv.reader(grupos_csv)

    for i, data in enumerate(csv_reader, start=1):
        group_name = data[0]
        group_cuit = data[1]
        db_name = group_name
        container_name = "pirra_" + str(i)
        
        # create db and migrate
        p1 = subprocess.Popen(["createdb", db_name])
        p1.wait()

        p2 = subprocess.Popen(["docker-compose", "exec", container_name, "python3", "manage.py", "migrate"])
        p2.wait()

        # create a user for the teacher in each group
        p3 = subprocess.Popen(
            [
                "docker-compose", "exec", container_name, "python3", "manage.py", "shell", "-c", 
                "from django.contrib.auth import get_user_model; User = get_user_model(); \
                    User.objects.create_superuser('carolina', 'carolina.guglielmotti@cpem17.com.ar', 'carito2626')"
            ]
        )
        p3.wait()

        # create a user for the group
        create_group_user = "from django.contrib.auth import get_user_model;\
            User = get_user_model(); User.objects.create_superuser('" + group_name + "', '', '" + group_cuit + "')"

        print("CREATING USER " + group_name + " TO GROUP " + group_name + " CREATED!")

        p4 = subprocess.Popen(["docker-compose", "exec", container_name, "python3", "manage.py", "shell", "-c", create_group_user])
        p4.wait()

        # create company
        p5 = subprocess.Popen(["docker-compose", "exec", container_name, "python3", "manage.py", "init_empresa", group_cuit, group_name])
        p5.wait()

        print("GROUP " + group_name + " CREATED!")