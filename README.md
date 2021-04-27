# checkStatusVodafoneMobileWifiR216
Programma in Python che richiede lo status della saponetta Vodafone per gestire la carica della batteria.
In base allo stato della batteria viene accesa/spenta una presa TP-Link HS1xx.

## Occorrente
 - Presa TP-Link HS1xx;
 - Python 3.5^;
 - requests;
 - account su https://ifttt.com ed app mobile per creare e modificare le istruzioni (solo se si vuole la notifica);
 - plugin python per gestire la presa TP-Link (ho usato HS100) https://github.com/vrachieru/tplink-smartplug-api.
 
## Installazione comune
```
pip3 install requests git+https://github.com/vrachieru/tplink-smartplug-api.git
```

## Utilizzo
Configurare il file _config_ ed il file _opzioniEmail_ come da template.
Eseguire lo script python _check.py_ con python3.

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
Dopo qualche mese dall'ultimo upload ho aggiornato il Mac e quindi ho dovuto installare di nuovo da capo. Trovando problemi nell'installazione ho pensato di abbandonare dryscrape ed adottare qualcosa di più supportato, tipo Selenium.
Preso dalla voglia di alleggerire tutto e di trovare un modo più rapido per il controllo della batteria ho riscritto il codice utilizzando solo delle (semplici) chiamate GET, prendendo prima il token e poi facendo richiesta delle statistiche.
EOStory
