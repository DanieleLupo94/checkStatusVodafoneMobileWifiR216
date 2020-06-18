import time
import urllib.request

import requests
from bs4 import BeautifulSoup
import dryscrape
# Uso quello che sta nella cartella perché ha il metodo di stop
from dryscrape import xvfb

# TODO: Forse non serve creare una sessine ogni volta
# FIXME: Il server di dryscape consuma risorse anche se il programma è in sleep
# FIXME: Aumentare il tempo di attesa
# TODO: Attraverso un cambionamento uniforme, calcolare una stima di velocità di carica e scarica

url = 'http://192.168.0.1/html/home.htm'
urlWebhook = 'https://maker.ifttt.com/trigger/CheckBatteria/with/key/crgmhm7kuG2plVg8e7W1_V'
dryscrape.start_xvfb()
session = dryscrape.Session()
inCarica = False

# Configurazione per access token
SKILL_CLIENT_ID = 'YOUR_SKILL_CLIENT_ID'
SKILL_CLIENT_SECRET = 'YOUR_SKILL_CLIENT_SECRET'
API_TOKEN_URL = 'https://api.amazon.com/auth/O2/token'


def stopAttendiStart(secondiAttesa):
    dryscrape.stop_xvfb()
    time.sleep(60 * secondiAttesa)
    dryscrape.start_xvfb()
    return controllaStato()


def controllaStato():
    print("[", time.asctime(time.localtime(time.time())), "] Visito la pagina ", url)
    session = dryscrape.Session()
    session.visit(url)
    print("[", time.asctime(time.localtime(time.time())),
          "] Attendo che venga caricata la pagina ", url)
    time.sleep(15)  # Attendo che venga caricata la pagina
    response = session.body()
    print("[", time.asctime(time.localtime(time.time())), "] Ho visitato la pagina")

    soup = BeautifulSoup(response, 'html.parser')
    # FIXME: Se la pagina non è caricata completamente, il div è vuoto. Aggiungere questo controllo

    # Recupero il div della percentuale
    divs = soup.find('div', class_='TR_BATTERY_STATUS')
    # Separo attraverso gli spazi
    stato = divs.get_text().rsplit(' ')
    # Prendo la parte della percentuale
    stato = stato[2]
    # Tolgo le parentesi ed il simbolo della percentuale
    stato = stato[1:-2]
    print("[", time.asctime(time.localtime(time.time())), "] Batteria: ", stato)
    stato = int(stato)

    # Se è in carica viene mostrata la gif di caricamento
    imgBatteria = soup.find('img', id='batteryLevelImage')
    imgBatteria = imgBatteria['src'].rsplit('/')[2]
    imgBatteria = imgBatteria.rsplit('?')[0]
    inCarica = (imgBatteria == 'batteryCharging.gif')
    print("[", time.asctime(time.localtime(time.time())), "] In carica: ", inCarica)

    if inCarica:
        if stato == 100:
            # TODO: Spegnere il caricabatteria
            requests.post(urlWebhook, json={
                          'value1': 'Batteria carica. Spegnere la presa'})
            controllaStato()
        print("[", time.asctime(time.localtime(time.time())),
              "] Attendo ", 100 - stato, " minuti")
        stopAttendiStart(100-stato)  # Attesa dinamica
    else:
        # TODO: Pensare ad un modo dinamico di calcolare il tempo di attesa in base alla velocità di scaricamento della batteria
        if stato < 11:
            print("[", time.asctime(time.localtime(time.time())),
                  "] Batteria scarica. Invio la notifica ed attendo 5 minuti.")
            # TODO: Far accendere la presa da Alexa
            # Chiamo il webhook per mandare la notifica
            session.visit(urlWebhook)
            requests.post(urlWebhook, json={
                          'value1': 'Batteria scarica. Accendere la presa'})
            time.sleep(60*5)  # Attesa di 5 minuti
            controllaStato()
        else:
            # Ho calcolato in questo modo l'attesa in modo da avere un'attesa massima quando è carica e poi decrescente insieme alla batteria
            attesa = 100 - (100 - stato)
            print("[", time.asctime(time.localtime(time.time())),
                  "] Attendo ", attesa, " minuti")
            stopAttendiStart(attesa)  # Attesa dinamica "inversa"


def richiediAccessToken():
    payload = "grant_type=client_credentials&scope=alexa:skill_messaging&client_id=$SKILL_CLIENT_ID&client_secret=$SKILL_CLIENT_SECRET"
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    richiestaToken = requests.post(
        API_TOKEN_URL, data=payload, headers=headers)
    print(richiestaToken)


def mandaMessaggioAccendi():
    return 0


def mandaMessaggioSpegni():
    return 0


controllaStato()
