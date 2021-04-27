import datetime
import sys
import time
import xml.etree.ElementTree as ET

import requests as req
# API smart plug kasa
from tplink_smartplug import SmartPlug

# Controllo se è stato passato il file di configurazione in input
if len(sys.argv) != 2:
    raise ValueError('Bisogna passare il file di configurazione.')

pathFile = sys.argv[1]

# Leggo i vari parametri della configurazione dal file passato in input
def getConfigurazione():
    fileConfig = open(pathFile)
    configurazioni = {}
    for line in fileConfig.read().splitlines():
        configurazioni[line.split(' = ')[0]] = line.split(' = ')[1]
        if configurazioni[line.split(' = ')[0]] == 'True':
                configurazioni[line.split(' = ')[0]] = True
        if configurazioni[line.split(' = ')[0]] == 'False':
            configurazioni[line.split(' = ')[0]] = False
    return configurazioni

# Cerco l'ultimo ip della presa conosciuto all'interno del file di log
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

# Provo a chiamare ogni dispositivo nella rete per cercare la presa
def bruteSearchPresa():
    baseIp = getConfigurazione()['baseIp']
    for x in range(100, 120):
        try:
            plug = SmartPlug(baseIp + str(x))
            plug.name
            return plug, (baseIp + str(x))
        except:
            continue

# Cerca la presa nel file di log altrimenti la cerca nella rete
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

# Compone la path del file di log e la restituisce
def getPathFileLog():
    pathIniziale = getConfigurazione()['pathInizialeFileLog']
    return pathIniziale + "logModemVodafone_" + (datetime.datetime.now().strftime("%Y%m%d"))

# Salvo il log nel file e lo chiudo subito
def salvaLog(testo):
    pathFileLog = getPathFileLog()
    fileLog = open(pathFileLog, "a+")
    # Aggiungo il timestamp al log
    t = "[" + time.asctime(time.localtime(time.time())) + "] " + str(testo)
    fileLog.write(t)
    fileLog.write("\n")
    # print(">> ", t)
    fileLog.close()
    #req.post(getConfigurazione()["urlOnlineLogWriter"], data={'riga': t, 'nomeFile':'test.txt'})

# Chiude il processo e manda le relative notifiche
def chiudiTutto():
    salvaLog('Killo il server.')
    req.post(getConfigurazione()['urlIFTTT'], json={'value1':'Killo il server.'})

# Controlla se il dispositivo è connesso ad internet
def checkConnection(host='http://google.com'):
    try:
        req.get(host)
        return True
    except:
        return False

# Se configurato, manda una notifica IFTTT
def sendNotificaIFTTT(testo):
    if (getConfigurazione()['usaIFTTT'] == True):
        req.post(getConfigurazione()['urlIFTTT'], json={'value1':str(testo)})

# Metodo principale dove recupera le informazioni sulla saponetta
# e sulla presa e decide se accendere o spegnere la presa.
def controlla():
    # Attendo 5 minuti se non c'è connessione
    while(checkConnection() == False):
        time.sleep(5 * 1000)
    urlModem = getConfigurazione()['url']
    r = req.get(urlModem)
    setCookie = r.headers['Set-Cookie'].split(';path')[0]
    r = req.get(getConfigurazione()['urlAPI'], headers = {'Cookie': setCookie})
    # Il contenuto della risposta ha bisogno di essere decodificato in UTF-8
    contenuto = r.content.decode('utf-8')
    root_node = ET.fromstring(contenuto)
    livelloBatteria = root_node.find('BatteryLevel').text
    inCarica = root_node.find('BatteryStatus').text
    # inCarica = 0 -> non sta caricando
    # inCarica = 1 -> sta caricando
    presa, ip = getPresa()
    if inCarica == "0":
        inCarica = False
    else:
        inCarica = True
    salvaLog("Batteria: " + livelloBatteria + ", sta caricando: " + str(inCarica) + ", ip " + ip + ", is_on " + str(presa.is_on))
    livelloBatteria = int(livelloBatteria)

    if inCarica:
        if livelloBatteria == 100:
            # Batteria carica
            salvaLog("Batteria carica")
            sendNotificaIFTTT("Batteria carica")
            presa.turn_off()
            controlla()
    else:
        if livelloBatteria < 20:
            # Batteria scarica
            salvaLog("Batteria scarica")
            sendNotificaIFTTT("Batteria scarica")
            presa.turn_on()
            controlla()
    # Attendo per il controllo
    minuti = getConfigurazione()['minutiAttesa']
    salvaLog("Attendo " + str(minuti) + " minuti.")
    minuti = int(minuti)
    time.sleep(60 * minuti)
    controlla()

# Fa in modo che lo script non venga mai terminato, nemmeno quando va in errore
def main():
    salvaLog('Avvia tutto')
    try:
        controlla()
    finally:
        chiudiTutto()

main()
