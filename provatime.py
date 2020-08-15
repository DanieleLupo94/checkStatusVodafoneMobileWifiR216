import time
from datetime import datetime, timedelta

t = time.asctime(time.localtime(time.time()))
nine_hours_from_now = datetime.now() + timedelta(hours=9)
t = time.asctime(time.localtime(nine_hours_from_now))
print(t)
