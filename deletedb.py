from sqlalchemy import create_engine, text

# Verbindung zur Datenbank erstellen
engine = create_engine('mysql+pymysql://root:1234@localhost')

# Verbindung herstellen und SQL-Befehl ausführen
with engine.connect() as connection:
    connection.execute(text("DROP DATABASE IF EXISTS our_users"))
    connection.execute(text("CREATE DATABASE our_users"))