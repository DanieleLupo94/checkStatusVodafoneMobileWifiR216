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

# TODO: Forse non serve creare una sessione ogni volta

# In base all'analisi fatta, decido il rateo con cui si scarica e si carica la batteria
rateoScaricamento = 1.5
rateoCaricamento = 2

pathIniziale = "/home/pi/GitProjects/checkStatusVodafoneMobileWifiR216/"

audioAccendi = pathIniziale + 'accendi_caricabatteria.mp3'
audioSpegni = pathIniziale + 'spegni_caricabatteria.mp3'

url = 'http://192.168.0.1/html/launch.htm'
urlAPI = 'http://192.168.0.1/api/monitoring/status'
urlWebhook = 'https://maker.ifttt.com/trigger/CheckBatteria/with/key/crgmhm7kuG2plVg8e7W1_V'

fileOpzioniEmail = open('opzioniEmail')
opzioni = {}
for line in fileOpzioniEmail.read().splitlines():
  opzioni[line.split(' = ')[0]] = line.split(' = ')[1]

baseIp = '192.168.0.'

def getPresa():
    for x in range(100,110):
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
            tempoAttesa = rateoCaricamento * (100 - livelloBatteria)
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
            attesa = 100 - (100 - livelloBatteria)
            attesa = attesa * rateoScaricamento
            ricontrollo = datetime.datetime.now() + datetime.timedelta(hours=int(attesa/60), minutes=attesa%60)
            salvaLog("Attendo " + str(attesa) + " minuti (" + ricontrollo.strftime("%x %X")  +")")
            attesa = attesa * 60
            time.sleep(attesa)
            controlla()

def chiudiTutto():
    salvaLog("Killo il server.", True)
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
    controlla()
finally:
    chiudiTutto()

