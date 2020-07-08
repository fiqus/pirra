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
        subprocess.call(["docker-compose", "exec", "-u", "postgres", "postgres", "createdb", db_name])
        subprocess.call(["docker-compose", "exec", container_name, "python3", "manage.py", "migrate"])

        # create a user for the teacher in each group
        subprocess.call(
            [
                "docker-compose", "exec", container_name, "python3", "manage.py", "shell", "-c", 
                "from django.contrib.auth import get_user_model; User = get_user_model(); \
                    User.objects.create_superuser('carolina', 'carolina.guglielmotti@cpem17.com.ar', 'carito2626')"
            ]
        )
        
        # create a user for the group
        create_group_user = "from django.contrib.auth import get_user_model;\
            User = get_user_model(); User.objects.create_superuser('" + group_name + "', '', '" + group_cuit + "')"
        subprocess.call(["docker-compose", "exec", container_name, "python3", "manage.py", "shell", "-c", create_group_user])

        # create company
        subprocess.call(["docker-compose", "exec", container_name, "python3", "manage.py", "init_empresa", group_cuit, group_name])
        print("GROUP " + group_name + " CREATED!")