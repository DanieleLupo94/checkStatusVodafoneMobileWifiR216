# from playsound import playsound
# import time
# playsound('accendi_caricabatteria.mp3', True)
# time.sleep(5)

import os

audioAccendi = './accendi_Caricabatteria.mp3'

os.system("omxplayer " + audioAccendi)
