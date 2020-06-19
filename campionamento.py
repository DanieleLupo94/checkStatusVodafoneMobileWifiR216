import time
import urllib.request
import signal

import requests
from bs4 import BeautifulSoup
import dryscrape
import webkit_server

url = 'http://192.168.0.1/html/home.htm'
urlWebhook = 'https://maker.ifttt.com/trigger/CheckBatteria/with/key/crgmhm7kuG2plVg8e7W1_V'

intervalloCampionamento = 10  # Minuti

# Configurazione del server in modo da evitare memory leak
dryscrape.start_xvfb()
server = webkit_server.Server()
server_conn = webkit_server.ServerConnection(server=server)
driver = dryscrape.driver.webkit.Driver(connection=server_conn)
session = dryscrape.Session(driver=driver)

inCarica = False


def controllaStato():
    session = dryscrape.Session()
    session.visit(url)
    time.sleep(15)  # Attendo che venga caricata la pagina
    response = session.body()
    session.reset()  # Per evitare il memory leak

    soup = BeautifulSoup(response, 'html.parser')

    # Recupero il div della percentuale
    divs = soup.find('div', class_='TR_BATTERY_STATUS')
    # Separo attraverso gli spazi
    stato = divs.get_text().rsplit(' ')
    # Prendo la parte della percentuale
    stato = stato[2]
    # Tolgo le parentesi ed il simbolo della percentuale
    stato = stato[1:-2]
    stato = int(stato)

    # Se è in carica viene mostrata la gif di caricamento
    imgBatteria = soup.find('img', id='batteryLevelImage')
    imgBatteria = imgBatteria['src'].rsplit('/')[2]
    imgBatteria = imgBatteria.rsplit('?')[0]
    inCarica = (imgBatteria == 'batteryCharging.gif')
    print(time.asctime(time.localtime(time.time())), ",", stato, ",", inCarica)

    time.sleep(60 * intervalloCampionamento)
    controllaStato()


try:
    print("Data, Batteria, Alimentazione")
    controllaStato()
finally:
    print("LOG [", time.asctime(time.localtime(time.time())),
          "] Killo il server")
    server.kill()  # Altrimenti resta attivo
