import global_vars as g
from util import *
import paho.mqtt.client as paho
import os
import time
import requests

mqtt_client = None

def mqtt_on_connect(client, userdata, flags, rc):
    """
    Callback function for MQTT client on connect event.
    """
    if rc == 0: 
        debug_log("Connected to mqtt broker - mqtt_on_connect")
        g.registered_entity = {}
    else:
        debug_log("Connection to mqtt broker failed - mqtt_on_connect")
        logger.warning("  Retry in 10 sec again")
        time.sleep(10)
        #mqtt_client.disconnect()
        #mqtt_connect()

def mqtt_disconnect():
    """
    Disconnects the MQTT client.
    """
    if g.run_mode != "hass":
        mqtt_client.disconnect()
    return True
        
def mqtt_connect():
    """
    Connects the MQTT client.
    """
    if g.run_mode == "hass":
        return True

    global mqtt_client
    response_ok = False
    while not response_ok:
        try:
            client = get_dict_value(g.config["mqtt"], "client", "nwsclient")
            mqtt_client = paho.Client(client)
            if get_dict_value(g.config["mqtt"], "username", "") != "":
                mqtt_client.username_pw_set(g.config["mqtt"]["username"], g.config["mqtt"]["password"])
            mqtt_client.on_connect = mqtt_on_connect
            res = mqtt_client.connect(g.config["mqtt"]["address"], g.config["mqtt"]["port"])
            mqtt_client.loop_start()
            if res != 0:
                logger.error(snow()+ "Cannot connect to mqtt broker: " + str(res))
                logger.error("  Retry in 1 min again")
                time.sleep(60)            
            else:
                debug_log("Connected to mqtt broker")
                response_ok = True
                g.registered_entity = {}
        except BaseException as err:
            logger.error(f"{snow()}Unexpected mqtt_connect {err=}, {type(err)=}")
            logger.error("  Retry in 1 min again")
            time.sleep(60)
    
    return True

def hass_mqtt_publish(topic, value, qos, retain):
    """
    Publishes a message to the MQTT broker.
    """
    headers = {'Authorization': f"Bearer {os.getenv('SUPERVISOR_TOKEN')}",'content-type': 'application/json' }
    data = {'payload': f"{value}", 'topic': f"{topic}", 'retain': f"{retain}"}
    #logger.debug(data)

    response_ok = False
    while not response_ok:
        if g.run_mode == "hass":
            try:
                res = requests.request('POST', 'http://supervisor/core/api/services/mqtt/publish', headers=headers, json=data)
                if res.status_code != 200:
                    logger.error(f"{snow()}Error hass_mqtt_publish, not nonnected? =>reconnect? code: {res.rc}  status_code: {res.status_code}")
                    logger.error(f"  {topic}={value}")
                    time.sleep(60)
                else:
                    response_ok = True
            except BaseException as err:
                logger.error(f"{snow()}Unexpected mqtt_publish {err=}, {type(err)=}")
                logger.error("  Retry in 1 min again")
                time.sleep(60)
            
        else:
            try:
                res = mqtt_client.publish(topic, value, qos, retain)
                if res.rc != 0:
                    logger.error(f"{snow()}Error hass_mqtt_publish, not nonnected? =>reconnect? code: {res.rc}")
                    logger.error(f"  {topic}={value}")
                    mqtt_connect()
                else:
                    response_ok = True
                    #print(f"  {topic}={value}")
            except BaseException as err:
                logger.error(f"{snow()}Unexpected mqtt_publish {err=}, {type(err)=}")
                logger.error("  Retry in 1 min again")
                time.sleep(60)
            
    return res

def hass_mqtt_delete_retain_messages():
    """
    Deletes the retained messages from the MQTT broker.
    """
    def on_message(client, userdata, msg):
        if msg.retain == 1:
            if get_dict_value(g.config["nfws"], "log_level") == "debug":
                logger.info(f"Deleting retain topic {msg.topic}")
            hass_mqtt_publish(msg.topic, "", 0, True)
#            hass_mqtt_publish("homeassistant/sensor/nfws/test", "", 0, True)
    global mqtt_client

    if g.run_mode == "hass":
        return
    if get_dict_value(g.config["nfws"], "deleteRetain", False) != True:
        return
    logger.info(snow() + "Deleting retain config messages")
    mqtt_client.subscribe("homeassistant/sensor/nfws/#")
    mqtt_client.on_message = on_message
    time.sleep(5)
    mqtt_client.unsubscribe("homeassistant/sensor/nfws/#")
