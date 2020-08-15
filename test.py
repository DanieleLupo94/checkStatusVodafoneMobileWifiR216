import time
import urllib.request
import signal

import requests
from bs4 import BeautifulSoup
import dryscrape
import webkit_server

url = 'https://developer.amazon.com/alexa/console/ask/test/amzn1.ask.skill.1bef177d-03ee-468a-9580-a17c3775b96a/development/it_IT'
dryscrape.start_xvfb()
server = webkit_server.Server()
server_conn = webkit_server.ServerConnection(server=server)
driver = dryscrape.driver.webkit.Driver(connection=server_conn)
session = dryscrape.Session(driver=driver)


def prova():
    session = dryscrape.Session()
    session.visit(url)
    time.sleep(15)  # Attendo che venga caricata la pagina
    response = session.body()
    soup = BeautifulSoup(response, 'html.parser')
    divs = soup.find('input', id='ap_email')
    print(divs)
    # print(response)


try:
    prova()
finally:
    print("[", time.asctime(time.localtime(time.time())),
          "] Killo il server")
    server.kill()  # Altrimenti resta attivo
