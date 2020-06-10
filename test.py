import time
import urllib.request

import requests
from bs4 import BeautifulSoup

url = 'http://192.168.0.1/html/home.htm'
response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')

divs = soup.findAll('div')

for d in divs:
    if d['class'] == 'rhsMenuText wordwrap TR_BATTERY_STATUS':
        print(d)
    else:
        print('Non è lui')
