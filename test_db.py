import psycopg2
from decouple import config

conn_params = {
    'dbname': config('DB_NAME', default='e_sugu'),
    'user': config('DB_USER', default='postgres'),
    'password': config('DB_PASSWORD', default='Confidence'),
    'host': config('DB_HOST', default='localhost'),
    'port': config('DB_PORT', default='5432'),
}

try:
    conn = psycopg2.connect(**conn_params)
    print("Connexion réussie !")
    conn.close()
except Exception as e:
    print(f"Erreur : {e}")