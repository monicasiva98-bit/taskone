# app/database.py




import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="taskone",
        user="postgres",
        password="annular",
        port=5432
    )
    return conn