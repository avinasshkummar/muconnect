# db.py
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:@localhost:5433/muconnect'

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn
