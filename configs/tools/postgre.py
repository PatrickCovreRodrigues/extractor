import os
import psycopg2
from sqlalchemy import create_engine

class RDSPostgreSQLManager:
    def __init__(self):
        self.db_name = "app_db"
        self.db_user = "app_user"
        self.db_password = "app_password"
        self.db_host = "172.26.13.184"
        self.db_port = "5432"

    def connect(self):
        try:
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
            )
            print("Conexão bem-sucedida ao banco de dados PostgreSQL.")
            print(connection.info)
            return connection
        except psycopg2.Error as e:
            print(f"Erro ao conectar ao banco de dados PostgreSQL: {e}")
            return None

    def execute_query(self, query):
        try:
            connection = self.connect()
            if connection:
                cursor = connection.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
                connection.commit()
                connection.close()
                return result
            else:
                print("Não foi possível estabelecer a conexão com o banco de dados.")
                return None
        except psycopg2.Error as e:
            print(f"Erro ao executar a consulta SQL: {e}")
            return None

    def execute_insert(self, query, values):
        try:
            connection = self.connect()
            if connection:
                cursor = connection.cursor()
                cursor.execute(query, values)
                connection.commit()
                cursor.close()
                connection.close()
                print("Inserção bem-sucedida.")
            else:
                print("Não foi possível estabelecer a conexão com o banco de dados.")
        except psycopg2.Error as e:
            print(f"Erro ao executar a inserção SQL: {e}")

    def alchemy(self):
        self.engine = create_engine(
            f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        return self.engine
