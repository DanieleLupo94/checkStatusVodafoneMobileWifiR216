import time
import urllib.request
import signal

import requests
from bs4 import BeautifulSoup
import dryscrape
import webkit_server
import os

# TODO: Forse non serve creare una sessione ogni volta
# TODO: Attraverso un campionamento uniforme, calcolare una stima di velocità di carica e scarica

# In base all'analisi fatta, decido il rateo con cui si scarica e si carica la batteria
rateoScaricamento = 1.5
rateoCaricamento = 2

audioAccendi = './accendi_caricabatteria.mp3'

audioSpegni = './spegni_caricabatteria.mp3'

attesaCaricamentoPagina = 30

pathFileLog = "./log"

url = 'http://192.168.0.1/html/home.htm'
urlWebhook = 'https://maker.ifttt.com/trigger/CheckBatteria/with/key/crgmhm7kuG2plVg8e7W1_V'

# Configurazione del server in modo da evitare memory leak
dryscrape.start_xvfb()
server = webkit_server.Server()
server_conn = webkit_server.ServerConnection(server=server)
driver = dryscrape.driver.webkit.Driver(connection=server_conn)
session = dryscrape.Session(driver=driver)

# fileLog = open(pathFileLog,"a+")

inCarica = False

def controllaStato():
    salvaLog("Creo la sessione e visito la pagina " + url)
    session = dryscrape.Session()
    session.visit(url)
    salvaLog("Attendo che venga caricata la pagina " + url)
    time.sleep(attesaCaricamentoPagina)  # Attendo che venga caricata la pagina
    response = session.body()
    session.reset()  # Per evitare il memory leak
    salvaLog("Ho visitato la pagina " + url)

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
    salvaLog("Batteria: " + stato)
    stato = int(stato)

    # Se è in carica viene mostrata la gif di caricamento
    imgBatteria = soup.find('img', id='batteryLevelImage')
    imgBatteria = imgBatteria['src'].rsplit('/')[2]
    imgBatteria = imgBatteria.rsplit('?')[0]
    inCarica = (imgBatteria == 'batteryCharging.gif')
    if (inCarica):
        salvaLog("In carica: true")
    else:
        salvaLog("In carica: false")

    if inCarica and stato != 100:
        tempoAttesa = rateoCaricamento * (100-stato)
        salvaLog("Attendo " + str(tempoAttesa) + " minuti")
        tempoAttesa = tempoAttesa * 60
        time.sleep(tempoAttesa)  # Attesa dinamica
        controllaStato()
    else:
        # TODO: Pensare ad un modo dinamico di calcolare il tempo di attesa in base alla velocità di scaricamento della batteria
        if stato < 11:
            salvaLog("Batteria scarica. Invio la notifica ed attendo 5 minuti.")
			# Riproduco il file audio in modo che Alexa senta il comando
            os.system("omxplayer " + audioAccendi)
            # Chiamo il webhook per mandare la notifica
            requests.post(urlWebhook, json={
                          'value1': 'Batteria scarica. Accendere la presa'})
            time.sleep(60*5)  # Attesa di 5 minuti
            controllaStato()
        else:
            if stato == 100:
				# Chiamo il webhook per mandare la notifica
                requests.post(urlWebhook, json={
                              'value1': 'Batteria carica. Spegnere la presa'})
				# Riproduco il comando in modo che Alexa possa sentirlo
                os.system("omxplayer " + audioSpegni)
            # Ho calcolato in questo modo l'attesa in modo da avere un'attesa massima quando è carica e poi decrescente insieme alla batteria
            attesa = 100 - (100 - stato)
            attesa = attesa * rateoScaricamento
            attesa = attesa
            salvaLog("Attendo " + str(attesa) + " minuti")
            # Attesa dinamica "inversa"
            attesa = attesa * 60
            time.sleep(attesa)
            controllaStato()


# Salvo il log nel file e lo chiudo subito
def salvaLog(testo):
	fileLog = open(pathFileLog,"a+")
	# Aggiungo il timestamp al log
	t = "[" + time.asctime(time.localtime(time.time())) + "] " + str(testo)
	fileLog.write(t)
	fileLog.write("\n")
	# print(">> ", t)
	fileLog.close()

try:
    controllaStato()
finally:
    salvaLog("Killo il server.")
    # fileLog.close()
    server.kill()  # Altrimenti resta attivo

