import csv
import os

from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

con = connect(dbname="", user="postgres", host="localhost", password="postgres")
con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = con.cursor()


with open("./first_batch.csv", "r") as grupos_csv:
    csv_reader = csv.reader(grupos_csv)

    for i, data in enumerate(csv_reader, start=1):
        group_name = data[0]

        cur.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public to " + group_name)
        cur.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public to " + group_name)
        cur.execute("GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public to " + group_name)

        print(group_name + " FIXED")

cur.close()
con.close()