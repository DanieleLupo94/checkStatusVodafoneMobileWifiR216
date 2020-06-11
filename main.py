import time
import urllib.request

import requests
from bs4 import BeautifulSoup
import dryscrape

url = 'http://192.168.0.1/html/home.htm'
urlWebhook = 'https://maker.ifttt.com/trigger/evento/with/key/crgmhm7kuG2plVg8e7W1_V'
dryscrape.start_xvfb()
session = dryscrape.Session()


def controllaStato():
    print("[", time.strftime("%x %X", time.gmtime()), "] Visito la pagina ", url)
    session.visit(url)
    time.sleep(15)  # Attendo che venga caricata la pagina
    response = session.body()
    print("[", time.strftime("%x %X", time.gmtime()), "] Ho visitato la pagina")

    soup = BeautifulSoup(response, 'html.parser')

    # Recupero il div della percentuale
    divs = soup.find('div', class_='TR_BATTERY_STATUS')

    # FIXME: Se la pagina non è caricata completamente, il div è vuoto. Aggiungere questo controllo

    # print(divs)

    # Separo attraverso gli spazi
    stato = divs.get_text().rsplit(' ')
    # Prendo la parte della percentuale
    stato = stato[2]
    # Tolgo le parentesi ed il simbolo della percentuale
    stato = stato[1:-2]

    # print(type(divs.get_text()))

    # print("Batteria ", stato)
    print("[", time.strftime("%x %X", time.gmtime()), "] Batteria: ", stato)
    stato = int(stato)

    # TODO: Pensare ad un modo dinamico di calcolare il tempo di attesa in base alla velocità di scaricamento della batteria
    if stato > 49:
        print("[", time.strftime("%x %X", time.gmtime()), "] Attendo 30 minuti")
        time.sleep(60*60)  # Attesa di 60 minuti
    elif stato < 50 and stato > 29:
        print("[", time.strftime("%x %X", time.gmtime()), "] Attendo 15 minuti")
        time.sleep(60*30)  # Attesa di 30 minuti
    elif stato < 30 and stato > 9:
        print("[", time.strftime("%x %X", time.gmtime()), "] Attendo 5 minuti")
        session.visit(urlWebhook)  # Chiamo il webhook per mandare la notifica
        time.sleep(60 * 5)  # Attesa di 5 minuti
    controllaStato()


controllaStato()
