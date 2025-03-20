from math import e
import os
import pandas as pd
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from sqlalchemy.sql import text 

# Load environment variables from .env
load_dotenv()



class Database:
    def __init__(self):
        "Inicia la conexión con la base de datos - PostgreSQL"
        self.db_name = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")

        self.db_url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        
        try:
            self.engine = create_engine(self.db_url)
            self.engine.connect()  # Prueba la conexión
            print(f"✅ Connected to PostgreSQL database: {self.db_name}")
        except SQLAlchemyError as e:
            print(f"❌ Error conectando a PostgreSQL: {e}")

        
    def get_sql_database(self, ):
       return SQLDatabase(engine=self.engine)
    
    def get_schema(self):
        """Retrieve tables and their column metadata from the public schema."""

        schema_info = {}

        with self.engine.connect() as conn:
            # Query to fetch detailed column information
            table_query = text("""  
                SELECT 
                    table_name, 
                    column_name, 
                    data_type, 
                    is_nullable, 
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    datetime_precision
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)  # Wrap query inside text()
            
            result = conn.execute(table_query)  # Now it works!

            for row in result.fetchall():
                table_name, column_name, data_type, is_nullable, column_default, char_max_len, num_precision, num_scale, datetime_precision = row

                if table_name not in schema_info:
                    schema_info[table_name] = []

                schema_info[table_name].append({
                    "column_name": column_name,
                    "data_type": data_type,
                    "is_nullable": is_nullable,
                    "column_default": column_default,
                    "max_length": char_max_len,
                    "numeric_precision": num_precision,
                    "numeric_scale": num_scale,
                    "datetime_precision": datetime_precision
                })

        return schema_info