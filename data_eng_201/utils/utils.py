import requests
import numpy as np
import pandas as pd
import re
import sqlite3
from sqlalchemy.orm import sessionmaker
import sqlalchemy
from datetime import datetime
import datetime
from bs4 import BeautifulSoup
import requests

BASE_URL = 'https://www.getonbrd.com/api/v0/categories'


def obtain_categories():
    df = pd.DataFrame()
    api = '?per_page=99999&page='
    for num in list(range(1,9999)):
        tags = requests.get(BASE_URL+'/'+api+str(num), verify=False)
        if tags.json().get('data'):
            df = pd.read_json(path_or_buf=tags.content, orient='split')
        else:
            break
    return df

def obtain_jobs(cat):
    df = pd.DataFrame()
    df_temp = []
    for categories in cat:
        api = '/'+categories+'/jobs?per_page=99999&page='

        for num in list(range(1,99999999)):
            tags = requests.get(BASE_URL+'/'+api+str(num)+'&expand=["company","tags"]', verify=False)
            if tags.json().get('data'):
                df_temp.append(pd.read_json(path_or_buf=tags.content, orient='split')) # split (best), columns NO, values NO, records NO, index NO
            else:
                break
        df = df_temp[0]
        for n in range(1, len(df_temp)):
            df = pd.concat([df, df_temp[n]], ignore_index=True)

        title,functions,desirable, description,  seniority = [], [], [], [], []

    final = pd.DataFrame(columns=['id', 'title', 'functions', 'desirable', 'description', 'seniority'])

    for dato in df['attributes']:
        title.append(dato['title'])
        description.append(dato['description'])
        functions.append(dato['functions'])
        desirable.append(dato['desirable'])
        seniority.append(dato['seniority'])
    
    final['id'] = df['id']
    final['title'] = title
    final['functions'] = functions
    final['desirable'] = desirable
    final['seniority'] = seniority
    final['description'] = description

    final['title'] = final['title'].str.replace('<[^<]+?>', '', regex=True)
    final['functions'] = final['functions'].str.replace('<[^<]+?>', '', regex=True)
    final['desirable'] = final['desirable'].str.replace('<[^<]+?>', '', regex=True)
    final['description'] = final['description'].str.replace('<[^<]+?>', '', regex=True)
    register_to_db('get_on_board', final)


def data_laborum():
    job_url = []
    for i in range(10): # no se analizara estrategia de paginacion
            works = requests.get('https://portal.chiletrabajos.cl/empresa/xinergia/ofertas/'+str(i)+'?categoria=informatica',verify=False)
            soup = BeautifulSoup(works.text, 'html.parser')
            all_link = soup.find_all('div',{'class':'col-sm-12 px-0'})
            if all_link:
                for i in range(len(all_link)):
                    job_url.append(all_link[i].find('a')['href'])
            else:
                print('No hay mas data')
                break
            

    job_data = []
    df = pd.DataFrame(columns=['id','title','functions','desirable','description','seniority'])

    for x in range(len(job_url)):
        work = requests.get(job_url[x], verify=False)
        soup = BeautifulSoup(work.text, 'html.parser')
        all_link = soup.find_all('span',{'class':'d-block ml-5'})
        if all_link:      
            job_data.append({ # objeto tipo para getonboard
                'title': re.sub('\W+', ' ', all_link[0].text),
                'functions':'',
                'desirable': re.sub('\W+', ' ', soup.find('div',{'class':'mt-2'}).text),
                'seniority':'',
                'description': re.sub('\W+', ' ', soup.find('p',{'class':'lead'}).text)
            })
        else:
            break


    for i in range(len(job_data)):
        df.loc[i]=[i,BeautifulSoup(job_data[i]['title'],'lxml').get_text(),job_data[i]['functions'],BeautifulSoup(job_data[i]['desirable'],'lxml').get_text(),job_data[i]['seniority'],BeautifulSoup(job_data[i]['description'],'lxml').get_text()]

    df['title'] = df['title'].str.replace('<[^<]+?>', '', regex=True)
    df['functions'] = df['functions'].str.replace('<[^<]+?>', '', regex=True)
    df['desirable'] = df['desirable'].str.replace('<[^<]+?>', '', regex=True)
    df['description'] = df['description'].str.replace('<[^<]+?>', '', regex=True)

    register_to_db('laborum', df)

def register_to_db(name, df):
    engine = sqlalchemy.create_engine('sqlite:///'+name+'.sqlite')
    conn = sqlite3.connect(name+'.sqlite')
    cursor = conn.cursor()

    sql_query = """
    CREATE TABLE IF NOT EXISTS {}(
        title VARCHAR(200),
        functions VARCHAR(200),
        desirable VARCHAR(200),
        description VARCHAR(200),
        seniority VARCHAR(200),
        CONSTRAINT PRIMARY_KEY_CONSTRAINT PRIMARY KEY (title)        
    )
    """.format(name)
    cursor.execute(sql_query)

    try:
        df.to_sql(name, engine, index=False, if_exists="append")
    except:
        print("Data already exists")
    conn.close()