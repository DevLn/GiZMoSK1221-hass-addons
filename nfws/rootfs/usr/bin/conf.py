import global_vars as g
import json
import os
import shutil
import yaml
from util import *

def prepare_hass_addon():
    """
    Prepare the Home Assistant add-on by creating necessary directories and copying files.
    """
    if g.run_mode != "hass":
        return False

    try:
        res = os.listdir(r'/config/')
        if not "nfws" in res:
            try:
                os.mkdir('/config/nfws')
            except BaseException as err:
                logger.critical('Cannot create directory /config/nfws')
                exit()
            try:
                shutil.copyfile('/usr/bin/stations.yaml', '/config/nfws/stations.yaml')
                #shutil.copyfile('stations_example.yaml', '/config/nfws/stations_example.yaml')
            except BaseException as err:
                logger.critical('Cannot copy stations.yaml to /config/nfws')
                exit()
            
    except BaseException as err:
        return False

    return True

def load_config():
    """
    Load the configuration settings from options.json or options.yaml file.
    """
    global params
    global logger

    if "SUPERVISOR_TOKEN" in os.environ:
        g.config_dir = "/config/nfws/"
        g.run_mode = "hass"
    else:
        g.run_mode = "local"

    prepare_hass_addon()

    if g.run_mode == "hass":
        try:
            with open('/data/options.json', 'r') as file:
                g.config = json.load(file)
        except BaseException as err:
            logger.critical(f"{snow()}/data/options.json missing {err=}, {type(err)=}")
            exit()
    else:
        try:
            with open(r'options.yaml') as file:
                g.config = yaml.load(file, Loader=yaml.FullLoader)
        except BaseException as err:
            logger.critical(f"{snow()}options.yaml missing {err=}, {type(err)=}")
            exit()
    
    #exit()

    try:
        with open(g.config_dir+r'stations.yaml') as file:
            config_stations = yaml.load(file, Loader=yaml.FullLoader)
    except BaseException as err:
        logger.critical(f"{snow()}{g.config_dir}stations.yaml missing {err=}, {type(err)=}")
        exit()
    g.config.update(config_stations)

    if get_dict_value(g.config["nfws"], "log_level") != "None":
        logger.setLevel(get_dict_value(g.config["nfws"], "log_level").upper())

    logger.debug(f"Run mode: {g.run_mode}")
    logger.debug(f"Config dir: {g.config_dir}")
    
    if "nfws" not in g.config:
        g.config["nfws"] = "None"
    if "netatmo" not in g.config:
        logger.critical("netatmo section in config missing")
        exit()
    if g.run_mode != "hass" and "mqtt" not in g.config:
        logger.critical("mqtt section in config missing")
        exit()
    if "netatmo_stations" not in g.config:
        logger.critical("netatmo_stations section in stations.yaml missing")
        exit()
    
    if g.config["netatmo"]["client_id"] == "":
        logger.critical("Netatmo client_id is empty!")
        exit()
    if g.config["netatmo"]["client_secret"] == "":
        logger.critical("Netatmo client_secret is empty!")
        exit()
    
    if "redirect_uri" not in g.config["netatmo"]:
        (g.config["netatmo"])["redirect_uri"] = "hassio"
    if "state" not in g.config["netatmo"]:
        (g.config["netatmo"])["state"] = "nfws_hass"

    g.netatmo_stations = g.config["netatmo_stations"]
    g.params = {
        'device_id': '00:00:00:00:00:00',
        'get_favorites': 'true',
    }
    g.params["device_id"] = next(iter(g.netatmo_stations))  #get first station from list
    #print(next(iter(netatmo_stations)))

    return True
