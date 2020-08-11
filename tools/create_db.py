import subprocess
import csv
import os

# get groups and format for template
with open("./grupos.csv", "r") as grupos_csv:
    csv_reader = csv.reader(grupos_csv)

    for i, data in enumerate(csv_reader, start=1):
        db_name = data[0]

        # create db and migrate
        p1 = subprocess.Popen(["createdb", db_name])
        p1.wait()

        print(db_name + " CREATED!")