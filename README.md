# checkStatusVodafoneMobileWifiR216
Programma in Python che fa scraping sulla home del dispositivo e controlla la percentuale della batteria.

## Occorrente
 - requests (pip install requests);
 - bs4 (pip install bs4);
 - dryscrape (https://github.com/niklasb/dryscrape), poiché il JS elabora lo stato della batteria;
 - qt (https://www.qt.io/offline-installers) per installare dryscrape;
 - webkit (https://github.com/niklasb/webkit-server);
 - https://stackoverflow.com/questions/38788816/pip-install-dryscrape-fails-with-error-errno-2-no-such-file-or-directory-s per i problemi durante l'installazione del webkit;
 - account su https://ifttt.com ed app mobile per creare e modificare le istruzioni;

Dopo aver contattato l'assistenza Amazon per dei problemi coi permessi per creare la skill Alexa, mi hanno detto che quello che voglio fare io non si può fare.
L'idea attuale è di riprodurre un audio della mia voce dicendo di accendere o spegne in base all'esigenza.
Ho deciso di usare playsound e serve Gst. Per installarlo ho usato questa guida http://lifestyletransfer.com/how-to-install-gstreamer-python-bindings/  .
Dato che la macchina virtuale di Linux per Windows (Ubuntu for Windows) non può riprodurre suoni, installo tutto su Windows.
Dato che per Windows è un casino installare qt, installo un player via shell sulla macchina Ubuntu.
 
## Altre fonti
 - esempio di utilizzo di dryscrape (https://stackoverflow.com/questions/8049520/web-scraping-javascript-page-with-python).

## Note
 - Ho utilizzato Pyhton3
