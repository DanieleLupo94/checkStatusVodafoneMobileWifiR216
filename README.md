# checkStatusVodafoneMobileWifiR216
Programma in Python che fa scraping sulla home del dispositivo e controlla la percentuale della batteria.
Dopo vari tentativi e problemi, mi sono spostato sul rasperry. Vedi la storia per saperne di più.
Dopo alcuni mesi ho riscritto il codice utilizzando le api del modem per recuperare le informazioni quindi _non viene più fatto scraping_.

## Occorrente
 - Presa TP-Link HS1xx;
 - Python 3.5^;
 - requests;
 - bs4;
 - qt4 (https://wiki.qt.io/Apt-get_Qt4_on_the_Raspberry_Pi);
 - dryscrape (https://github.com/niklasb/dryscrape), poiché ~~il JS elabora lo stato della batteria~~ serve la sessione per mantenere il token;
 - account su https://ifttt.com ed app mobile per creare e modificare le istruzioni (solo se si vuole la notifica);
 - plugin python per gestire la presa TP-Link (ho usato HS100) https://github.com/vrachieru/tplink-smartplug-api.
 
## Installazione
Modulo requests
```
pip3 install requests
```
Modulo bs4
```
pip3 install bs4
```
Qt4
```
sudo apt-get install qt4-dev-tools qtcreator
```
Dryscrape
```
sudo apt-get install qt5-default libqt5webkit5-dev build-essential python-lxml xvfb
pip3 install dryscrape
```
Plugin Python per le API della presa wifi
```
pip3 install git+https://github.com/vrachieru/tplink-smartplug-api.git
```

## Utilizzo
Eseguire lo script python _apiCheck.py_ con la versione di python 3.5 o superiore (vedi dryscrape e qt4).

## Storia
Dopo aver contattato l'assistenza Amazon per dei problemi coi permessi per creare la skill Alexa, mi hanno detto che quello che voglio fare non si può fare.
L'idea attuale è di riprodurre un audio della mia voce dicendo di accendere o spegnere in base all'esigenza.
Ho deciso di usare playsound e serve Gst. Per installarlo ho usato questa guida http://lifestyletransfer.com/how-to-install-gstreamer-python-bindings/  .
Dato che la macchina virtuale di Linux per Windows (Ubuntu for Windows) non può riprodurre suoni, installo tutto su Windows.
Dato che per Windows è un casino installare qt, installo un player via shell sulla macchina Ubuntu.
Dopo aver installato il player sulla macchina Ubuntu, continua a non trovare la periferica di audio quindi mi sono spostato sul raspberry.
Una volta sul raspberry, l'unico problema riscontrato è stato installare qt5. Dato che anche qt4 ha il qmake (che serve a dryscrape), ho installato qt4 con un solo comando.
Una volta provato il codice, ho inserito un service all'avvio che si occupa di mantenere in vita lo script.
Dopo alcuni mesi ho analizzato le chiamate http effettuate dalla pagina principale per recuperare le informazioni. In questo modo ho trovato la chiamata che permette di ricevere molte informazioni tra cui: se è in carica, lo stato della batteria ed il livello del segnale. Ho riscritto il codice, facendo un po' di pulizia, utilizzando 2 chiamate fondamentali: la prima permette di ricevere il token mentre la seconda riceve le informazioni richieste.
Dopo un po' di tempo ho contattato il supporto TP-Link per chiedere se avesso implementato una API per controllare la presa da remoto e mi hanno risposto dicendo che su GitHub ci sono repository dove, attraverso il reverse engineering, hanno creato delle API. In particolare mi sono interessato alla verisione Python. Purtroppo la presa che avevo inizialmente utilizza un protocollo troppo sicuro quindi ho comprato il modello TP-Link HS100. In questo modo con le API del modem posso sapere lo stato della batteria mentre con quelle della presa posso sapere se è in carica.
EOStory
 
## Altre fonti
 - esempio di utilizzo di dryscrape (https://stackoverflow.com/questions/8049520/web-scraping-javascript-page-with-python).

## Note
 - ho utilizzato Pyhton3.5 inizialmente e poi 3.7;
 - il tutto gira su un Raspberry 3B+ con Raspian Jessie e poi Raspbian GNU/Linux 10 (buster);
 - utilizzo un service all'avvio per avviare lo script e riavviarlo se crasha (quando non riceve il token).
