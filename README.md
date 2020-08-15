# checkStatusVodafoneMobileWifiR216
Programma in Python che fa scraping sulla home del dispositivo e controlla la percentuale della batteria.
Dopo vari tentativi e problemi, mi sono spostato sul rasperry. Vedi la storia per saperne di più.

## Occorrente
 - requests (pip install requests);
 - bs4 (pip install bs4);
 - dryscrape (https://github.com/niklasb/dryscrape), poiché il JS elabora lo stato della batteria;
 - <del>qt (https://www.qt.io/offline-installers) per installare dryscrape;</del>
 - qt4 (https://wiki.qt.io/Apt-get_Qt4_on_the_Raspberry_Pi);
 - webkit (https://github.com/niklasb/webkit-server);
 - https://stackoverflow.com/questions/38788816/pip-install-dryscrape-fails-with-error-errno-2-no-such-file-or-directory-s per i problemi durante l'installazione del webkit;
 - account su https://ifttt.com ed app mobile per creare e modificare le istruzioni (solo se si vuole la notifica).

## Utilizzo
Eseguire lo script python con la versione di python 3.5 o superiore (vedi dryscrape e qt4).

## Storia
Dopo aver contattato l'assistenza Amazon per dei problemi coi permessi per creare la skill Alexa, mi hanno detto che quello che voglio fare non si può fare.
L'idea attuale è di riprodurre un audio della mia voce dicendo di accendere o spegne in base all'esigenza.
Ho deciso di usare playsound e serve Gst. Per installarlo ho usato questa guida http://lifestyletransfer.com/how-to-install-gstreamer-python-bindings/  .
Dato che la macchina virtuale di Linux per Windows (Ubuntu for Windows) non può riprodurre suoni, installo tutto su Windows.
Dato che per Windows è un casino installare qt, installo un player via shell sulla macchina Ubuntu.
Dopo aver installato il player sulla macchina Ubuntu, continua a non trovare la periferica di audio quindi mi sono spostato sul raspberry.
Una volta sul raspberry, l'unico problema riscontrato è stato installare qt5. Dato che anche qt4 ha il qmake (che serve a dryscrape), ho installato qt4 con un solo comando.
Una volta provato il codice, ho inserito un service all'avvio che si occupa di mantenere in vita lo script.
EOStory
 
## Altre fonti
 - esempio di utilizzo di dryscrape (https://stackoverflow.com/questions/8049520/web-scraping-javascript-page-with-python).

## Note
 - ho utilizzato Pyhton3.5;
 - il tutto gira su un Raspberry 3B+ con Raspian Jessie;
 - utilizzo delle casse esterne collegate al raspberry;
 - utilizzo un service all'avvio per avviare lo script e riavviarlo se crasha (quando non carica in tempo la pagina oppure non c'è connessione).
