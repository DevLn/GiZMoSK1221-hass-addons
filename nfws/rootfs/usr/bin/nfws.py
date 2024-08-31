import time
from config import *
from util import *
from auth import *
from mqtt import *
from netatmo import *

load_config()
load_netatmo_token()
netatmo_check_oauth_code()

mqtt_connect()
netatmo_get_oauth_token()
hass_mqtt_delete_retain_messages()
mqtt_disconnect()

while True:
    logger.debug(snow() + "get data")

    mqtt_connect()

    json_netatmo = netatmo_getdata()
    json_netatmo_body = json_netatmo["body"]
    #print(json_netatmo_body)
    json_netatmo_devices = json_netatmo_body["devices"]
    #print(json_netatmo_devices)

    netatmo_handle_favourite_stations_sensors()
    netatmo_handle_calculated_sensors()

    mqtt_disconnect()        
    time.sleep(60*get_dict_value(config["netatmo"], "refresh_interval", 1))
