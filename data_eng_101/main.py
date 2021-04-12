from utils.utils import obtain_categories, obtain_jobs


def data():
    df_categories = obtain_categories()
    obtain_jobs(df_categories['id'])

data()