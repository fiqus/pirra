import csv
import os

from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

con = connect(dbname="", user="postgres", host="localhost", password="postgres")
con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = con.cursor()


with open("./all_groups.csv", "r") as grupos_csv:
    csv_reader = csv.reader(grupos_csv)

    for i, data in enumerate(csv_reader, start=1):
        group_name = data[0]
        group_cuit = data[1]

        cur.execute("CREATE DATABASE " + group_name)
        cur.execute("CREATE USER " + group_name + " WITH ENCRYPTED PASSWORD '" + group_cuit + "'")
        cur.execute("GRANT ALL PRIVILEGES ON DATABASE " + group_name + " TO " + group_name)

        print(group_name + " CREATED!")

cur.close()
con.close()