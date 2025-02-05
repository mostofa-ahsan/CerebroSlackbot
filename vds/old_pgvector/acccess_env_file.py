import os
import subprocess
import psycopg2
from dotenv import load_dotenv


dotenv_path= os.path.abspath("../../../.env")
load_dotenv(dotenv_path=dotenv_path)


# DB_USER = "dbuser"
# DB_PASSWORD = "-6vK_BURtfpZ_-PJxs32Fm2k "
# DB_PORT = "5432"
# DB_NAME = "vdsdata"
# DB_HOST = "127.0.0.1"

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")



print("DB_USER: ", DB_USER)
print("DB_PASSWORD: ", DB_PASSWORD)
print("DB_PORT: ", DB_PORT)
print("DB_NAME: ", DB_NAME)
print("DB_HOST: ", DB_HOST)
