import time
import datetime
import urllib.request
import signal
from sys import exit
import requests
import os
import smtplib
import ssl

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from mimetypes import guess_type
from email.encoders import encode_base64
from getpass import getpass

# API smart plug kasa
from tplink_smartplug import SmartPlug

# Inizializzo tutte le variabili
# Path che va anteposta davanti alle altre path
pathIniziale = ""
# File usati per il comando audio (che ora è commentato)
audioAccendi = ""
audioSpegni = ""
# Pagina principale del modem
url = ""
# Pagina delle API sullo status
urlAPI = ""
# URL webhook di IFTTT per le notifiche
urlWebhook = ""
# Parte iniziale degli IP con cui cercheremo la presa nella rete
baseIp = ""
# Velocità con cui si carica/scarica la batteria
percentualeScaricamentoAlMinuto = ""
percentualeCaricamentoAlMinuto = ""
# Sessione di dryscrape
session = None
# Oggetto che mantiene le configurazioni
configurazioni = {}

def caricaConfigurazioni():
    fileConfig = open('config')
    global configurazioni
    configurazioni = {}
    for line in fileConfig.read().splitlines():
        configurazioni[line.split(' = ')[0]] = line.split(' = ')[1]
        if configurazioni[line.split(' = ')[0]] == 'True':
            configurazioni[line.split(' = ')[0]] = True
        if configurazioni[line.split(' = ')[0]] == 'False':
            configurazioni[line.split(' = ')[0]] = False
    global pathIniziale
    pathIniziale = configurazioni['pathIniziale']
    global audioAccendi
    audioAccendi = pathIniziale + configurazioni['audioAccendi']
    global audioSpegni
    audioSpegni = pathIniziale + configurazioni['audioSpegni']
    global url
    url = configurazioni['url']
    global urlAPI
    urlAPI = configurazioni['urlAPI']
    global urlWebhook
    urlWebhook = configurazioni['urlWebhook']
    global baseIp
    baseIp = configurazioni['baseIp']
    global percentualeScaricamentoAlMinuto
    percentualeScaricamentoAlMinuto = float(configurazioni['percentualeScaricamentoAlMinuto'])
    global percentualeCaricamentoAlMinuto
    percentualeCaricamentoAlMinuto = float(configurazioni['percentualeCaricamentoAlMinuto'])

fileOpzioniEmail = open('opzioniEmail')
opzioni = {}
for line in fileOpzioniEmail.read().splitlines():
    opzioni[line.split(' = ')[0]] = line.split(' = ')[1]

def recuperaUltimoIpConosciutoPresa():
    pathFileLog = getPathFileLog()
    try:
        fileLog = open(pathFileLog, "r")
        lines = fileLog.readlines()
        for indice in range(len(lines)-1,0,-1):
            line = lines[indice]
            if "Presa PresaSmart" in line:
                return line[line.find("ip ") + 3: line.find(", is_on")]
        return ""
    except FileNotFoundError:
        return ""

def bruteSearchPresa():
    for x in range(100, 120):
        try:
            plug = SmartPlug(baseIp + str(x))
            plug.name
            return plug, (baseIp + str(x))
        except:
            continue

def getPresa():
    #return bruteSearchPresa()
    # Recupero l'ultimo ip utilizato dalla presa
    vecchioIp = recuperaUltimoIpConosciutoPresa()
    if ("192" in vecchioIp):
        try:
            plug = SmartPlug(vecchioIp)
            # Provo ad accede al nome. Va in eccezione se non è la presa
            plug.name
            return plug, vecchioIp
        except:
            # Ha cambiato ip
            return bruteSearchPresa()
    else:
        # Non riesce a trovare l'ip nel file 
        return bruteSearchPresa()

class Email(object):
    ''' A class for send a mail (with attachment) through an 
        SSL SMTP server. The test code work on Raspberry PI 3B+
    '''

    def __init__(self, from_address, to_address, subject, message, image=None):
        # Email data
        self.from_address = from_address
        self.to_address = to_address

        # Create the email object
        self.email = MIMEMultipart()

        self.email['From'] = from_address
        self.email['To'] = to_address
        self.email['Subject'] = subject

        text = MIMEText(message, 'plain')
        self.email.attach(text)

        # Manage attachments
        if image != None:
            attachment = MIMEBase('image', 'jpg')
            attachment.set_payload(image)
            encode_base64(attachment)
            attachment.add_header('Content-Disposition',
                                  'attachment',
                                  "image.jpg")

            self.email.attach(attachment)

        # Put all email contents in a string
        self.message = self.email.as_string()

    def send(self, username, password):
        # Server data
        server = opzioni['MAIL_SERVER']
        port = opzioni['MAIL_PORT']

        # Connection
        context = ssl.create_default_context()
        connection = smtplib.SMTP_SSL(server, port, context=context)
        connection.login(username, password)

        # Send the message
        connection.sendmail(self.from_address,
                            self.to_address,
                            self.message)

        # Close
        connection.close()

# Compone la path del file di log e la restituisce
def getPathFileLog():
    return pathIniziale + "APIlog" + (datetime.datetime.now().strftime("%Y%m%d"))

# Salvo il log nel file e lo chiudo subito
def salvaLog(testo, conEmail=False):
    pathFileLog = getPathFileLog()
    fileLog = open(pathFileLog, "a+")
    # Aggiungo il timestamp al log
    t = "[" + time.asctime(time.localtime(time.time())) + "] " + str(testo)
    fileLog.write(t)
    fileLog.write("\n")
    # print(">> ", t)
    fileLog.close()
    if conEmail and configurazioni['notificaEmail']:
        email = Email(opzioni['FROM_ADDRESS'],
                      opzioni['TO_ADDRESS'], "Monitoring modem wifi", t)
        email.send(opzioni['MAIL_USER'], opzioni['MAIL_PASSWORD'])

def notificaIFTTT(testo = ""):
    if configurazioni['notificaIFTTT']:
        requests.post(urlWebhook, json={'value1': testo})

def controlla():
    if not checkConnection():
        time.sleep(60 * 5)  # Attendo 5 minuti
        controlla()
    # Ricarico le configurazioni per aggiornare, eventualmente, i parametri del caricamento/scaricamento
    caricaConfigurazioni()
    if configurazioni['metodo'] == 'dryscrape':
        livelloBatteria, caricando, segnale = getInformazioniDalleAPIModemDryscrape()
    elif configurazioni['metodo'] == 'Selenium':
        livelloBatteria, caricando, segnale = getInformazioniDalleAPIModemSelenium()
    
    # Controllo se la presa è accesa per determinare se è in carica
    plug, ip = getPresa()
    salvaLog("Presa " + plug.name + ", ip " + ip + ", is_on " + str(plug.is_on))
    inCarica = plug.is_on

    salvaLog("Segnale: " + segnale + ", batteria: " + livelloBatteria)

    livelloBatteria = int(livelloBatteria)

    if inCarica:
        if livelloBatteria == 100:
            salvaLog("Batteria carica", True)
            notificaIFTTT("Batteria carica. Spegnere la presa.");
            # os.system("omxplayer -o local " + audioSpegni)
            plug.turn_off()
            controlla()
        else:
            if (bool(configurazioni['controlloStatico'])):
                tempoAttesa = int(configurazioni['secondiControlloStatoStatico'])
                tempoAttesa = tempoAttesa / 60
            else:  
                # Si carica dello 0,45% al minuto
                tempoAttesa = 100 - livelloBatteria
                tempoAttesa = tempoAttesa / percentualeCaricamentoAlMinuto
                tempoAttesa = int(tempoAttesa)
            ricontrollo = datetime.datetime.now() + datetime.timedelta(hours=int(tempoAttesa/60), minutes=tempoAttesa % 60)
            salvaLog("Attendo " + str(tempoAttesa) + " minuti (" + ricontrollo.strftime("%x %X") + ")")
            tempoAttesa = tempoAttesa * 60
            time.sleep(tempoAttesa)
            controlla()
    else:
        if livelloBatteria < 11:
            salvaLog("Batteria scarica", True)
            notificaIFTTT('Batteria scarica. Accendere la presa')
            # os.system("omxplayer -o local " + audioAccendi)
            plug.turn_on()
            controlla()
        else:
            if (configurazioni['controlloStatico']):
                attesa = int(configurazioni['secondiControlloStatoStatico'])
                attesa = attesa / 60
            else:
                # Si scarica dello 0,35% al minuto -> (batteria restante)/0,35 = minuti restanti
                # Batteria restante
                attesa = livelloBatteria - 13
                # Tempo restante fino al 13% di batteria
                attesa = attesa / percentualeScaricamentoAlMinuto
                attesa = int(attesa)
            ricontrollo = datetime.datetime.now() + datetime.timedelta(hours=int(attesa/60), minutes=attesa % 60)
            salvaLog("Attendo " + str(attesa) + " minuti (" + ricontrollo.strftime("%x %X") + ")")
            attesa = attesa * 60
            time.sleep(attesa)
            controlla()


def chiudiTutto():
    salvaLog("Killo il server.", True)
    # fileLog.close()
    # server.kill()  # Altrimenti resta attivo
    if (configurazioni['notificaIFTTT']):
        requests.post(urlWebhook, json={'value1': 'Qualquadra non cosa. Killo il server'})
    main()


def checkConnection(host='http://google.com'):
    try:
        urllib.request.urlopen(host)  # Python 3.x
        return True
    except:
        return False

def getInformazioniDalleAPIModemDryscrape():
    import xml.etree.ElementTree as ET
    # Visito la pagina principale per prendere il token
    session.visit(url)
    response = session.body()
    # Visito la pagina delle API con tutte le informazioni
    session.visit(urlAPI)
    # Leggo la risposta, che è in XML
    response = session.body()
    # TODO: Controllare nel caso in cui non avessi il token
    # print(str(response))

    # Attraverso il parser recupero le informazioni dall'XML
    root = ET.fromstring(response)
    b = root.find('body')
    response = b.find('response')
    segnale = response.find('signalicon').text    
    batteria = response.find('batterypercent').text
    inCarica = response.find('batterystatus').text
    return batteria, inCarica, segnale

def getInformazioniDalleAPIModemSelenium():
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.expected_conditions import presence_of_element_located
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.firefox.options import Options
    
    options = Options()
    options.add_argument('-headless')
    driver = webdriver.Firefox(options = options)
    wait = WebDriverWait(driver, 10)
    driver.get(url)
    driver.get(urlAPI)
    wait.until(presence_of_element_located((By.TAG_NAME, "response")))
    batteria = driver.find_element_by_tag_name("batterypercent").text
    inCarica = driver.find_element_by_tag_name("batterystatus").text
    segnale = driver.find_element_by_tag_name("signalicon").text
    driver.close()
    driver.quit()
    return batteria, inCarica, segnale

def main():
    caricaConfigurazioni()
    salvaLog("Avvio tutto")
    if configurazioni['metodo'] == 'dryscrape':
        from bs4 import BeautifulSoup
        import dryscrape
        import webkit_server
        
        dryscrape.start_xvfb()
        server = webkit_server.Server()
        server_conn = webkit_server.ServerConnection(server=server)
        driver = dryscrape.driver.webkit.Driver(connection=server_conn)
        global session
        session = dryscrape.Session(driver=driver)
    elif configurazioni['metodo'] == 'Selenium':
        import platform
        
        # Lo deve fare solo la prima volta
        if 'raspberry' not in platform.uname().node:
            import geckodriver_autoinstaller
            geckodriver_autoinstaller.install()
    try:
        controlla()
    except Exception as e:
        print('Eccezione:', e)
        exit()
    finally:
        chiudiTutto()



main()
