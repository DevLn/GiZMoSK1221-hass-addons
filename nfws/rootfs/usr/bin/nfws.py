import global_vars as g
import time
from conf import *
from util import *
from auth import *
from mqtt import *
from netatmo import *

load_config()

logger.debug('config loaded:')
logger.debug(g.config)
logger.debug('netatmo_stations loaded:')
logger.debug(g.netatmo_stations)
logger.debug('params loaded:')
logger.debug(g.params)

load_netatmo_token()

logger.debug('netatmo_token loaded:')
logger.debug(g.netatmo_token)

netatmo_check_oauth_code()

mqtt_connect()
netatmo_get_oauth_token()

logger.debug('netatmo_token refreshed:')
logger.debug(g.netatmo_token)


hass_mqtt_delete_retain_messages()
mqtt_disconnect()

while True:
    logger.debug(snow() + "get data")

    mqtt_connect()

    hass_register_sensor_test()

    json_netatmo = netatmo_getdata()
    json_netatmo_body = json_netatmo["body"]
    #print(json_netatmo_body)
    json_netatmo_devices = json_netatmo_body["devices"]
    #print(json_netatmo_devices)

    netatmo_handle_favourite_stations_sensors()
    netatmo_handle_calculated_sensors()

    mqtt_disconnect()
    time.sleep(60*get_dict_value(g.config["netatmo"], "refresh_interval", 1))
