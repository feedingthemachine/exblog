import requests
import numpy as np
import pandas as pd
import re

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
    final.to_csv('jobs.csv', sep='*')