import time
import datetime
import urllib.request
import signal
from sys import exit

import requests
from bs4 import BeautifulSoup
import dryscrape
import webkit_server
import os
import _thread

# TODO: Forse non serve creare una sessione ogni volta

# In base all'analisi fatta, decido il rateo con cui si scarica e si carica la batteria
rateoScaricamento = 1.5
rateoCaricamento = 2

pathIniziale = "/home/pi/GitProjects/checkStatusVodafoneMobileWifiR216/"

audioAccendi = pathIniziale + 'accendi_caricabatteria.mp3'
audioSpegni = pathIniziale + 'spegni_caricabatteria.mp3'

attesaCaricamentoPagina = 60

# TODO: Far cambiare la data del file di log automaticamente
pathFileLog = pathIniziale + "log" + (datetime.datetime.now().strftime("%Y%m%e"))

url = 'http://192.168.0.1/html/home.htm'
urlWebhook = 'https://maker.ifttt.com/trigger/CheckBatteria/with/key/crgmhm7kuG2plVg8e7W1_V'

# Configurazione del server in modo da evitare memory leak
dryscrape.start_xvfb()
server = webkit_server.Server()
server_conn = webkit_server.ServerConnection(server=server)
driver = dryscrape.driver.webkit.Driver(connection=server_conn)
session = dryscrape.Session(driver=driver)

inCarica = False

def controllaStato():
    # Controllo se c'è la connessione. Se è offline, attendo un minuto e riprovo
    if not checkConnection():
        salvaLog("Nessuna connessione. Attendo 1 minuto e ricontrollo.")
        time.sleep(60)
        controllaStato()
    _thread.start_new_thread(controllaProblema, ())
    salvaLog("Creo la sessione e visito la pagina " + url)
    session = dryscrape.Session()
    session.visit(url)
    # FIXME: Catturare EndOfStreamError()
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
        ricontrollo = datetime.datetime.now() + datetime.timedelta(hours=int(tempoAttesa/60), minutes=tempoAttesa%60)
        salvaLog("Attendo " + str(tempoAttesa) + " minuti (" + ricontrollo.strftime("%x %X") + ")")
        tempoAttesa = tempoAttesa * 60
        time.sleep(tempoAttesa)  # Attesa dinamica
        controllaStato()
    else:
        # TODO: Pensare ad un modo dinamico di calcolare il tempo di attesa in base alla velocità di scaricamento della batteria
        if stato < 11:
            salvaLog("Batteria scarica. Invio la notifica ed attendo 5 minuti.")
			# Riproduco il file audio in modo che Alexa senta il comando
            os.system("omxplayer -o local " + audioAccendi)
            # Chiamo il webhook per mandare la notifica
            requests.post(urlWebhook, json={'value1': 'Batteria scarica. Accendere la presa'})
            time.sleep(60*1)  # Attesa di 1 minuto
            controllaStato()
        else:
            if stato == 100:
                # FIXME: Il dispositivo potrebbe non rispondere quindi bisogna controllare che sia davvero in carica
				# Chiamo il webhook per mandare la notifica
                requests.post(urlWebhook, json={'value1': 'Batteria carica. Spegnere la presa'})
				# Riproduco il comando in modo che Alexa possa sentirlo
                os.system("omxplayer -o local " + audioSpegni)
                # TODO fare più sistemato
                # Ripeto il comando poiché a volte non funziona subito
                time.sleep(60)
                os.system("omxplayer -o local " + audioSpegni)
            # Ho calcolato in questo modo l'attesa in modo da avere un'attesa massima quando è carica e poi decrescente insieme alla batteria
            attesa = 100 - (100 - stato)
            attesa = attesa * rateoScaricamento
            ricontrollo = datetime.datetime.now() + datetime.timedelta(hours=int(attesa/60), minutes=attesa%60)
            salvaLog("Attendo " + str(attesa) + " minuti (" + ricontrollo.strftime("%x %X")  +")")
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

def controllaProblema():
	attesa = 60 * 2
	time.sleep(attesa)
	fileLog = open(pathFileLog, "r")
	lastLine = fileLog.readlines()[-1]
	fileLog.close()
	salvaLog('>> Last line: ' + lastLine)
	if ("Creo la sessione" in lastLine or "Ho visitato la pagina" in lastLine):
		salvaLog('Rilevato problema')
		controllaStato()

def chiudiTutto():
    salvaLog("Killo il server.")
    # fileLog.close()
    server.kill()  # Altrimenti resta attivo
    requests.post(urlWebhook, json={'value1': 'Qualquadra non cosa. Killo il server'})

def checkConnection(host='http://google.com'):
    try:
        urllib.request.urlopen(host) #Python 3.x
        return True
    except:
        return False

try:
    controllaStato()
finally:
    chiudiTutto()

