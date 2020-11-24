import time
import datetime
import urllib.request
import signal
from sys import exit
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import dryscrape
import webkit_server
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

fileConfig = open('config')
configurazioni = {}
for line in fileConfig.read().splitlines():
  configurazioni[line.split(' = ')[0]] = line.split(' = ')[1]

fileOpzioniEmail = open('opzioniEmail')
opzioni = {}
for line in fileOpzioniEmail.read().splitlines():
  opzioni[line.split(' = ')[0]] = line.split(' = ')[1]

# Path che va anteposta davanti alle altre path
pathIniziale = configurazioni['pathIniziale']

# File usati per il comando audio (che ora è commentato)
audioAccendi = pathIniziale + configurazioni['audioAccendi']
audioSpegni = pathIniziale + configurazioni['audioSpegni']

# Pagina principale del modem
url = configurazioni['url']
# Pagina delle API sullo status
urlAPI = configurazioni['urlAPI']
# URL webhook di IFTTT per le notifiche
urlWebhook = configurazioni['urlWebhook']
# Parte iniziale degli IP con cui cercheremo la presa nella rete
baseIp = configurazioni['baseIp']

# Velocità con cui si carica/scarica la batteria
percentualeScaricamentoAlMinuto = float(configurazioni['percentualeScaricamentoAlMinuto'])
percentualeCaricamentoAlMinuto = float(configurazioni['percentualeCaricamentoAlMinuto'])
rateoCaricamento = 3.5
rateoScaricamento = 4

def getPresa():
    for x in range(100,120):
        try:
            plug = SmartPlug(baseIp + str(x))
            plug.name
            return plug, (baseIp + str(x))
        except:
            continue

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
            attachment = MIMEBase('image','jpg')
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


def getPathFileLog():
    return pathIniziale + "APIlog" + (datetime.datetime.now().strftime("%Y%m%d"))

# Salvo il log nel file e lo chiudo subito
def salvaLog(testo, conEmail = False):
    pathFileLog = getPathFileLog()
    fileLog = open(pathFileLog,"a+")
    # Aggiungo il timestamp al log
    t = "[" + time.asctime(time.localtime(time.time())) + "] " + str(testo)
    fileLog.write(t)
    fileLog.write("\n")
    # print(">> ", t)
    fileLog.close()
    if conEmail:
        email = Email(opzioni['FROM_ADDRESS'], opzioni['TO_ADDRESS'], "Monitoring modem wifi", t)
        email.send(opzioni['MAIL_USER'], opzioni['MAIL_PASSWORD'])

salvaLog("Avvio tutto")
dryscrape.start_xvfb()
server = webkit_server.Server()
server_conn = webkit_server.ServerConnection(server=server)
driver = dryscrape.driver.webkit.Driver(connection=server_conn)
session = dryscrape.Session(driver=driver)

def controlla():
    if not checkConnection():
        time.sleep(60 * 5) # Attendo 5 minuti
        controlla()
    # Visito la pagina principale per prendere il token
    session.visit(url)
    response = session.body()
    # print(str(response))
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
    
    # Controllo se la presa è accesa per determinare se è in carica
    plug, ip = getPresa()
    salvaLog("Presa " + plug.name + ", ip " + ip + ", is_on " + str(plug.is_on))
    inCarica = plug.is_on
    
    livelloBatteria = response.find('batterypercent').text
    
    salvaLog("Segnale: " + segnale + ", batteria: " + livelloBatteria)
    
    livelloBatteria = int(livelloBatteria)
    
    if inCarica:
        if livelloBatteria == 100:
            salvaLog("Batteria carica", True)
            requests.post(urlWebhook, json={'value1': 'Batteria carica. Spegnere la presa'})
            # os.system("omxplayer -o local " + audioSpegni)
            plug.turn_off()
            controlla()
        else:
            # Si carica dello 0,45% al minuto
            tempoAttesa = 100 - livelloBatteria
            tempoAttesa = tempoAttesa / percentualeCaricamentoAlMinuto
            tempoAttesa = int(tempoAttesa)
            ricontrollo = datetime.datetime.now() + datetime.timedelta(hours=int(tempoAttesa/60), minutes=tempoAttesa%60)
            salvaLog("Attendo " + str(tempoAttesa) + " minuti (" + ricontrollo.strftime("%x %X")  +")")
            tempoAttesa = tempoAttesa * 60
            time.sleep(tempoAttesa)
            controlla()
    else:
        if livelloBatteria < 11:
            salvaLog("Batteria scarica", True)
            requests.post(urlWebhook, json={'value1': 'Batteria scarica. Accendere la presa'})
            # os.system("omxplayer -o local " + audioAccendi)
            plug.turn_on()
            controlla()
        else:
            # Si scarica dello 0,35% al minuto -> (batteria restante)/0,35 = minuti restanti
            # Batteria restante
            attesa = livelloBatteria - 13
            # Tempo restante fino al 13% di batteria
            attesa = attesa / percentualeScaricamentoAlMinuto
            attesa = int(attesa)
            ricontrollo = datetime.datetime.now() + datetime.timedelta(hours=int(attesa/60), minutes=attesa%60)
            salvaLog("Attendo " + str(attesa) + " minuti (" + ricontrollo.strftime("%x %X")  +")")
            attesa = attesa * 60
            time.sleep(attesa)
            controlla()

def chiudiTutto():
    salvaLog("Killo il server.", True)
    # fileLog.close()
    # server.kill()  # Altrimenti resta attivo
    requests.post(urlWebhook, json={'value1': 'Qualquadra non cosa. Killo il server'})
    main()

def checkConnection(host='http://google.com'):
    try:
        urllib.request.urlopen(host) #Python 3.x
        return True
    except:
        return False

def main():    
    try:
        controlla()
    finally:
        chiudiTutto()



main()
