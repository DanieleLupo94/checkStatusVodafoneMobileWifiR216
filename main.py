import time
import urllib.request

import requests
from bs4 import BeautifulSoup
import dryscrape

url = 'http://192.168.0.1/html/home.htm'
urlWebhook = 'https://maker.ifttt.com/trigger/CheckBatteria/with/key/crgmhm7kuG2plVg8e7W1_V'
dryscrape.start_xvfb()
session = dryscrape.Session()
inCarica = False
ultimaPercentuale = -1


def controllaStato(ultimaPercentuale=-1):
    print("[", time.asctime(time.localtime(time.time())), "] Visito la pagina ", url)
    session.visit(url)
    time.sleep(15)  # Attendo che venga caricata la pagina
    response = session.body()
    print("[", time.asctime(time.localtime(time.time())), "] Ho visitato la pagina")

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
    print("[", time.asctime(time.localtime(time.time())), "] Batteria: ", stato)
    stato = int(stato)

    if ultimaPercentuale == -1:
        ultimaPercentuale = stato

    print("[", time.asctime(time.localtime(time.time())),
          "] Ultima percentuale: ", ultimaPercentuale)
    inCarica = (stato > ultimaPercentuale)

    print("[", time.asctime(time.localtime(time.time())), "] In carica: ", inCarica)

    if inCarica:
        if stato == 100:
            # TODO: Spegnere il caricabatteria
            requests.post(urlWebhook, json={
                          'value1': 'Batteria carica. Spegnere la presa'})
            inCarica = False
            ultimaPercentuale = stato
            controllaStato(ultimaPercentuale)
        print("[", time.asctime(time.localtime(time.time())),
              "] Attendo ", 100 - stato, " minuti")
        time.sleep(60*(100-stato))  # Attesa dinamica
        ultimaPercentuale = stato
        controllaStato(ultimaPercentuale)
    else:
        # TODO: Pensare ad un modo dinamico di calcolare il tempo di attesa in base alla velocità di scaricamento della batteria
        if stato < 11:
            print("[", time.asctime(time.localtime(time.time())),
                  "] Batteria scarica. Invio la notifica ed attendo 5 minuti.")
            # Chiamo il webhook per mandare la notifica
            session.visit(urlWebhook)
            requests.post(urlWebhook, json={
                          'value1': 'Batteria scarica. Accendere la presa'})
            time.sleep(60*5)  # Attesa di 5 minuti
        else:
            """ Ho calcolato in questo modo l'attesa in modo da avere un'attesa massima quando è carica e poi decrescente insieme alla batteria """
            attesa = 100 - (100 - stato)
            print("[", time.asctime(time.localtime(time.time())),
                  "] Attendo ", attesa, " minuti")
            time.sleep(60*attesa)  # Attesa dinamica "inversa"
        ultimaPercentuale = stato
        controllaStato(ultimaPercentuale)


controllaStato()
