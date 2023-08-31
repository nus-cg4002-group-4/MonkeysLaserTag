from bluepy import btle 

# Beetle 1: D0:39:72:E4:8E:67
beetle1 = "D0:39:72:E4:8E:67"
fakebeetle = "D0:39:72:E4:8E:68"

def bleConnect(beetle):
    try: 
        p = btle.Peripheral(beetle)
        print("Success!")
        print(p)
    except:
        print("Could not connect.")

bleConnect(beetle1)
bleConnect(fakebeetle)
from bluepy import btle

beetle1 = "D0:39:72:E4:8E:67"

def bleConnect(beetle):
    try:
        p = btle.Peripheral(beetle)
        print("Connection successful with details:")
        print(p)
    except:
        print("Unable to connect to beetle")
        # Error handling - timeout

bleConnect(beetle1)

# setDelegate
# waitForNotifications 

