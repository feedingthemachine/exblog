import requests
from bs4 import BeautifulSoup

url = 'http://www.imdb.com/title/tt0944947/episodes'

r = requests.get(url, params={'season': season})
soup = BeautifulSoup(r.text, 'html.parser')
print(soup)
