from logging import raiseExceptions
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from utils.utils import obtain_categories, obtain_jobs, data_laborum
from airflow.utils.helpers import chain, cross_downstream
import pandas as pd
import string
import re
import sqlite3
from sqlalchemy.orm import sessionmaker
import sqlalchemy
import pandas as pd

default_arguments = {'owner': 'Feedingthemachine', 'start_date': days_ago(1)}

with DAG(
    'get_on_board_laborum_scrapper_to_ai',
    schedule_interval= '@daily', 
    catchup=False,
    default_args=default_arguments
) as dag:
    # Called from utils.utils    
    def data_get_on_board():
        """
        This function call the API from gob and mix the responses
        """
        df_categories = obtain_categories()
        obtain_jobs(df_categories['id'])

    # Alternativily to a integrity test, i want know if i have data to ingest
    def check_data():
        query = """
        select count(id) FROM laborum
        """

        query2 = """
        select count(id) FROM get_on_board
        """
        # Connection for laborum
        conn = sqlite3.connect('laborum.sqlite')
        cursor = conn.cursor()
        result1 = cursor.execute(query)
        # Connection for get_on_boars
        conn2 = sqlite3.connect('get_on_board.sqlite')
        cursor2 = conn2.cursor()
        result2 = cursor2.execute(query2)

        # Just check if there are more than 0 results for all db
        if result1.fetchone()[0] > 0 and result2.fetchone()[0] > 0:
            print('extraccion correcta')

        else:
            raiseExceptions('Extraccion Erronea')

        conn.close()
        conn2.close()

    def send_to_raw():
        """
        This function make the Load part of ETL, take all the registrys and send to another db
        """

        query = """
        select * FROM laborum
        """

        query2 = """
        select * FROM get_on_board
        """
        conn = sqlite3.connect('laborum.sqlite')
        conn2 = sqlite3.connect('get_on_board.sqlite')
        # Destiny bbdd
        engine3 = sqlalchemy.create_engine('sqlite:///works.sqlite')
        conn3 = sqlite3.connect('works.sqlite')
        
        df = pd.read_sql(query, con=conn)
        df2 = pd.read_sql(query2, con=conn2)

        sql_query = """
            CREATE TABLE IF NOT EXISTS works(
                title VARCHAR(200),
                functions VARCHAR(200),
                desirable VARCHAR(200),
                description VARCHAR(200),
                seniority VARCHAR(200)
            )
            """
        cursor3 = conn3.cursor()
        cursor3.execute(sql_query)

        df = df.drop(columns=['id'])
        df2 = df2.drop(columns=['id'])

        df.to_sql('works', engine3, index=False, if_exists="append")
        df2.to_sql('works', engine3, index=False, if_exists="append")

        conn.close()
        conn2.close()
        conn3.close()
        print("Ingesta a raw finalizada")


    pyhton_get_on_board = PythonOperator(
        task_id='get_on_board', 
        python_callable=data_get_on_board, 
    )

    python_laborum = PythonOperator(
        task_id='laborum',
        python_callable=data_laborum
    )

    pyhton_check_data = PythonOperator(
        task_id='check_data',
        python_callable=check_data
    )

    phyton_to_raw = PythonOperator(
        task_id='raw_data',
        python_callable=send_to_raw
    )

    # La idea es realizar la tarea paralela, pero debes configurar tu airflow
    pyhton_get_on_board >> python_laborum >> pyhton_check_data >>  phyton_to_raw

