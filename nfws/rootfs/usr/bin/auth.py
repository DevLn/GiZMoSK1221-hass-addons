import global_vars as g
from log import logger
from util import *
import requests
import time
import webbrowser

def load_netatmo_token():
    """
    Load the Netatmo token from the netatmo_token.yaml file.
    If the file doesn't exist or there is an error, initialize an empty token.
    """
    try:
        with open(g.config_dir+r'netatmo_token.yaml') as file:
            g.netatmo_token = yaml.load(file, Loader=yaml.FullLoader)
    except BaseException as err:
        g.netatmo_token = {}
    
    #print(netatmo_token)
    
    if "refresh_token" not in g.netatmo_token:
        g.netatmo_token["refresh_token"] = ""
    if "access_token" not in g.netatmo_token:
        g.netatmo_token["access_token"] = ""

    return True

def netatmo_check_oauth_code():
    """
    Check if the Netatmo authorization OAUTH code is missing.
    If missing, display a critical error message with instructions on how to obtain the code.
    """
    #global config

    logger.debug('config auth code:')
    logger.debug(g.config)

    client = get_dict_value(g.config["netatmo"], "oauth_code", "")
    if client == "":
        logger.critical(f"{snow()}Missing Netatmo authorisation OAUTH code!")
        logger.critical(f"When access granted, copy code value from returned url to config.yaml")
        logger.critical(f"Example of returned URL: https://app.netatmo.net/oauth2/hassio?state=nfws_hass&code=5ebbe91cdd814823ddfe4336a7e9b6b8")
        client_id = g.config["netatmo"]["client_id"]
        uri = g.config["netatmo"]["redirect_uri"]
        state = g.config["netatmo"]["state"]
        url = f"https://api.netatmo.com/oauth2/authorize?client_id={client_id}&redirect_uri={uri}&scope=read_station&state={state}"
        logger.critical(f"")
        logger.critical(f"Calling...{url}")
        webbrowser.open_new(url)
        logger.critical(f"Copy&paste the url to a new window and get your OAUTH code")
        exit()
        
    return 1

def netatmo_get_oauth_token():
    """
    Get the Netatmo OAuth token based on the provided configuration.
    """

    client_id = g.config["netatmo"]["client_id"]
    client_secret = g.config["netatmo"]["client_secret"]
    uri = g.config["netatmo"]["redirect_uri"]
    code = g.config["netatmo"]["oauth_code"]
    refresh_token = g.netatmo_token["refresh_token"]
    
    if refresh_token != "":
        data = f"grant_type=refresh_token&client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}"
        method = "Netatmo refresh_token"
    else:
        data = f"grant_type=authorization_code&client_id={client_id}&client_secret={client_secret}&code={code}&redirect_uri={uri}&scope=read_station"
        method = "Netatmo authorization_code"

    #logger.debug(data)
    headers = {'Content-Type': 'application/x-www-form-urlencoded',}
    response_ok = False

    while not response_ok:
        try:
            response = requests.post('https://api.netatmo.com/oauth2/token', headers=headers, data=data)
        except BaseException as err:
            logger.error(f"{snow()}Unexpected {method} {err=}, {type(err)=}")
            logger.error("  Retry in 1 min again")
            time.sleep(60) 
            continue

        if response.status_code != requests.codes.ok:
            logger.warning(f"{method}: Wrong response code {response.status_code}")
            json_token=response.json()
            logger.warning(json_token)
            logger.warning("  Retry in 1 min again")
            time.sleep(60)
            continue
    
        json_token = response.json()
        logger.debug(json.dumps(json_token, indent = 4, sort_keys=True))
        if "access_token" not in json_token:
            logger.warning(snow() + f"{method}: Acces token is missing in response")
            logger.warning("  Retry in 1 min again")
            time.sleep(60)
            continue
        response_ok = True
        g.netatmo_token = response.json()
        
        #access_token = json_token["access_token"]
        #refresh_token = json_token["refresh_token"]

        try:
            with open(g.config_dir+r'netatmo_token.yaml', 'w') as file:
                documents = yaml.dump(json_token, file)
        except BaseException as err:
            logger.critical(f"{snow()}Cannot write netatmo_token.yaml {err=}, {type(err)=}")
            time.sleep(60)
            exit()

    return 1

def netatmo_refresh_token():
    """
    Refresh the Netatmo OAuth token based on the provided configuration.
    """
    
    logger.debug('refresh token:')
    logger.debug(g.config)


    client_id = g.config["netatmo"]["client_id"]
    client_secret = g.config["netatmo"]["client_secret"]
    refresh_token = g.netatmo_token["refresh_token"]
    
    data = f"grant_type=refresh_token&client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}"
    print(data)
    headers = {'Content-Type': 'application/x-www-form-urlencoded',}
    response_ok = False

    while not response_ok:
        try:
            response = requests.post('https://api.netatmo.com/oauth2/token', headers=headers, data=data)
        except BaseException as err:
            print(f"{snow()}Unexpected netatmo_refresh_token {err=}, {type(err)=}")
            json_token=response.json()
            print(json_token)
            print("  Retry in 1 min again")
            time.sleep(60)
            continue

        if response.status_code != requests.codes.ok:
            print(f"Netatmo_refresh_token: Wrong response code {response.status_code}")
            json_token=response.json()
            print(json_token)
            print("  Retry in 1 min again")
            time.sleep(60)
            continue
    
        json_token=response.json()
        print(json_token)
        print(json.dumps(json_token, indent = 4, sort_keys=True))
        if "access_token" not in json_token:
            print(snow() + "Netatmo_getdata: Acces token is missing in response")
            print("  Retry in 1 min again")
            time.sleep(60)
            continue
        response_ok = True
            
        #access_token = json_token["access_token"]
        g.netatmo_token = response.json()
        
        try:
            with open(g.config_dir+r'netatmo_token.yaml', 'w') as file:
                documents = yaml.dump(json_token, file)
        except BaseException as err:
            print(f"{snow()}Cannot write netatmo_token.yaml {err=}, {type(err)=}")
            exit()
        
    return 1