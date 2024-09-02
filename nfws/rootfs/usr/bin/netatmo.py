import global_vars as g
from jsonpath_ng.ext import parse
import json
import yaml
from util import *
from auth import *
from mqtt import *

netatmo_not_used_stations = []

json_netatmo = None
json_netatmo_body = None
json_netatmo_devices = None

def hass_register_sensor(entity_name, sensor, station):
    """
    Registers a sensor in Home Assistant.

    Args:
        entity_name (str): The name of the entity.
        sensor (str): The name of the sensor.
        station (str): The name of the station.

    Returns:
        bool: True if the sensor is successfully registered, False otherwise.
    """

    if entity_name in g.registered_entity:
        return False

    g.registered_entity[entity_name] = True
    hass_conf = {}
    hass_conf["unique_id"] = entity_name
    hass_conf["name"] = entity_name
    hass_conf["state_topic"] = "nfws/sensor/" + entity_name + "/state"
    hass_conf["json_attributes_topic"] = "nfws/sensor/" + entity_name + "/state" #new
    hass_conf["value_template"] = "{{ value_json.value }}" #new
    # hass_conf["device"] = {
    #     "identifiers": ["Netatmo weather station_70ee50"],
    #     "name": "Netatmo Favourite Weather Stations",
    #     "manufacturer": "Netatmo",
    #     "model": "Weather Stations"
    # }
    # set different device for each station
    hass_conf["device"] = {
        "identifiers": ["nfws_" + station],
        "name": station,
        "manufacturer": "Netatmo",
        "model": "Weather Stations"
    }


    sensor_lower = sensor.lower()
    if "compass" in sensor_lower:
        hass_conf["device_class"] = "enum"
        hass_conf["icon"] = "mdi:compass-rose"
        if sensor_lower[:4] == "wind":
            hass_conf["friendly_name"] = "Wind Direction"
        if sensor_lower[:8] == "max_wind":
            hass_conf["friendly_name"] = "Wind (Max) Direction"
        elif sensor_lower[:4] == "gust":
            hass_conf["friendly_name"] = "Gust Direction"

        if sensor_lower[-6:] == "symbol":
            hass_conf["friendly_name"] += " (↕)"
    else:
        hass_conf["state_class"] = "measurement"

        if sensor_lower == "temperature" or sensor_lower == "min_temp" or sensor_lower == "max_temp":
            hass_conf["device_class"] = "temperature"
            hass_conf["unit_of_measurement"] = "°C"
            hass_conf["friendly_name"] = "Temperature"
            if sensor_lower == "min_temp":
                hass_conf["friendly_name"] += " (Min)"
            elif sensor_lower == "max_temp":
                hass_conf["friendly_name"] += " (Max)"
        elif sensor_lower == "humidity":
            hass_conf["device_class"] = "humidity"
            hass_conf["unit_of_measurement"] = "%"
            hass_conf["friendly_name"] = "Humidity"
        elif sensor_lower == "pressure":
            hass_conf["device_class"] = "atmospheric_pressure"
            hass_conf["unit_of_measurement"] = "hPa"
            hass_conf["friendly_name"] = "Pressure"
        elif sensor_lower == "guststrength" or sensor_lower == "windstrength" or sensor_lower == "max_wind_str":
            hass_conf["device_class"] = "wind_speed"
            hass_conf["unit_of_measurement"] = "km/h"
            if sensor_lower == "windstrength":
                #hass_conf["icon"] = "mdi:weather-windy"
                hass_conf["friendly_name"] = "Wind Strength"
            elif sensor_lower == "max_wind_str":
                #hass_conf["icon"] = "mdi:weather-windy"
                hass_conf["friendly_name"] = "Wind (Max) Strength"
            else:
                hass_conf["icon"] = "mdi:weather-dust"
                hass_conf["friendly_name"] = "Gust Strength"
        elif "rain" in sensor_lower:
            hass_conf["device_class"] = "precipitation" #"water"
            hass_conf["state_class"] = "total_increasing"
            hass_conf["unit_of_measurement"] = "mm"
            hass_conf["friendly_name"] = "Rain"
            if "sum_rain_1" in sensor_lower:
                hass_conf["friendly_name"] += " (1h)"
            elif "sum_rain_24" in sensor_lower:
                hass_conf["friendly_name"] += " (24h)"
        elif "angle" in sensor_lower:
            hass_conf["device_class"] = "power_factor"
            hass_conf["unit_of_measurement"] = "°"
            #hass_conf["icon"] = "mdi:compass-rose"
            if sensor_lower == "windangle":
                hass_conf["friendly_name"] = "Wind Angle"
            elif sensor_lower == "max_wind_angle":
                hass_conf["friendly_name"] = "Wind (Max) Angle"
            elif sensor_lower == "gustangle":
                hass_conf["friendly_name"] = "Gust Angle"

    if "friendly_name" in hass_conf:
        hass_conf["name"] = hass_conf["friendly_name"]
    else:
        logger.debug( snow() + "Friendly name missing: " + str(hass_conf["name"]))

    logger.info( snow() + "Registering: " + str(hass_conf))
    ret = hass_mqtt_publish("homeassistant/sensor/nfws/" + entity_name + "/config", json.dumps(hass_conf), qos=0, retain=True)
    #print(ret.rc)

    return True

def hass_publish_station_sensor(station, sensor, value):
    """
    Publishes the sensor data for a specific station to Home Assistant.

    Args:
        station (dict): The configuration for the station.
        sensor (str): The name of the sensor.
        value (float): The value of the sensor.

    Returns:
        bool: True if the sensor data is successfully published, False otherwise.
    """
    if sensor in station["sensors"]:
        # Check if the sensor is configured for the station
        hass_register_sensor("nfws_" + station["name"] + "_" + sensor, sensor, station["name"])

        hass_data = {}
        hass_data["value"] = value
        hass_data["updated_when"] = snow()

        if "angle" in sensor.lower() and "compass" not in sensor.lower():
            hass_data["Compass"] = degToCompass(value)
            hass_data["CompassSymbol"] = degToCompassSymbol(value)

        ret = hass_mqtt_publish(f"nfws/sensor/nfws_{station['name']}_{sensor}/state", json.dumps(hass_data, ensure_ascii=False), qos = 0, retain = False)
        #print(ret.rc)
    return True

def hass_publish_calculated_station_sensor(entity_name, sensor, value, station):
    """
    Publishes the calculated station sensor data to Home Assistant.

    Args:
        entity_name (str): The name of the entity.
        sensor (str): The name of the sensor.
        value (dict): The sensor value to be published.
        station (str): The name of the station.

    Returns:
        bool: True if the sensor data is successfully published, False otherwise.
    """
    hass_register_sensor(entity_name, sensor, station)

    value["updated_when"] = snow()
    ret = hass_mqtt_publish(f"nfws/sensor/{entity_name}/state", json.dumps(value, ensure_ascii=False), qos = 0, retain = False)
    #print(ret.rc)

    return True

def netatmo_getdata():
    """
    Retrieves data from the Netatmo API.

    Returns:
        dict: The JSON response from the API.
    """
    response_ok = False;
    while not response_ok:
        access_token = g.netatmo_token["access_token"]
        headers = {'Authorization': f"Bearer {access_token}", }
        try:
            response = requests.get('https://api.netatmo.com/api/getstationsdata', params=g.params, headers=headers)
        except BaseException as err:
            logger.warning(f"{snow()}Unexpected netatmo_getdata {err=}, {type(err)=}")
            logger.warning("  Retry in 1 min again")
            time.sleep(60)
            continue
        json_netatmo = response.json()
        #print(json_netatmo)
        if get_dict_value(config["netatmo"], "show_response", False) == True:
            #print(json.dumps(json_netatmo, indent = 4, sort_keys=True))
            logger.debug(json_netatmo)
            time.sleep(60)

        if "error" in json_netatmo:
            if json_netatmo["error"]["message"] in {"Invalid access token", "Access token expired"}:
                logger.warning(snow() + "Invalid access token or expired:" + json_netatmo["error"]["message"])
                time.sleep(60)
                netatmo_get_oauth_token()
            else:
                logger.error(snow() + json_netatmo["error"]["message"])
                logger.error("  Retry in 1 min again")
                time.sleep(60)
        else:
            response_ok = True
    return json_netatmo

def netatmo_handle_favourite_stations_sensors():
    """
    Handle the favorite stations and their sensors from Netatmo API response.
    """
    for device in json_netatmo_devices:
        if device["_id"] not in g.netatmo_stations:
            if device["_id"] not in netatmo_not_used_stations:
                logger.info(f"Not used station id: {device['_id']}, name: {device['station_name']}")
                netatmo_not_used_stations.append(device["_id"])
            continue
        if device["reachable"] == False:
            continue

        #print(device["station_name"])
        #print(netatmo_stations[device["_id"]])

        hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "Pressure", device["dashboard_data"]["Pressure"])
        #print(device["dashboard_data"]["Pressure"])
        for module in device["modules"]:
            #print(module["data_type"])
            if module["reachable"] == False:
                continue
            if "data_type" not in module:
                continue
            if "dashboard_data" not in module:
                continue

            if module["data_type"].count("Temperature")!=0:
                if "Temperature" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "Temperature", module["dashboard_data"]["Temperature"])
                if "min_temp" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "min_temp", module["dashboard_data"]["min_temp"])
                if "max_temp" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "max_temp", module["dashboard_data"]["max_temp"])
            if module["data_type"].count("Humidity")!=0:
                if "Humidity" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "Humidity", module["dashboard_data"]["Humidity"])
                    #print(module["dashboard_data"]["Humidity"])
            if module["data_type"].count("Rain")!=0:
                if "Rain" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "rain", module["dashboard_data"]["Rain"])
                    #print(module["dashboard_data"]["Rain"])
                if "sum_rain_1" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "sum_rain_1", module["dashboard_data"]["sum_rain_1"])
                    #print(module["dashboard_data"]["sum_rain_1"])
                if "sum_rain_24" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "sum_rain_24", module["dashboard_data"]["sum_rain_24"])
                    #print(module["dashboard_data"]["sum_rain_24"])
            if module["data_type"].count("Wind")!=0:
                if "WindStrength" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "WindStrength", module["dashboard_data"]["WindStrength"])
                    #print(module["dashboard_data"]["WindStrength"])
                if "WindAngle" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "WindAngle", module["dashboard_data"]["WindAngle"])
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "WindAngleCompass", degToCompass(module["dashboard_data"]["WindAngle"]))  ##odkial fuka
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "WindAngleCompassSymbol", degToCompassSymbol(module["dashboard_data"]["WindAngle"]))  ##odkial fuka
                    #print(module["dashboard_data"]["WindAngle"])
                if "max_wind_angle" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "max_wind_angle", module["dashboard_data"]["max_wind_angle"])
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "max_wind_angleCompass", degToCompass(module["dashboard_data"]["max_wind_angle"]))  ##odkial fuka
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "max_wind_angleCompassSymbol", degToCompassSymbol(module["dashboard_data"]["max_wind_angle"]))  ##odkial fuka
                    #print(module["dashboard_data"]["WindAngle"])
                if "GustStrength" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "GustStrength", module["dashboard_data"]["GustStrength"])
                    #print(module["dashboard_data"]["GustStrength"])
                if "GustAngle" in module["dashboard_data"]:
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "GustAngle", module["dashboard_data"]["GustAngle"])
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "GustAngleCompass", degToCompass(module["dashboard_data"]["GustAngle"]))
                    hass_publish_station_sensor(g.netatmo_stations[device["_id"]], "GustAngleCompassSymbol", degToCompassSymbol(module["dashboard_data"]["GustAngle"]))
                    #print(module["dashboard_data"]["GustAngle"])

def netatmo_handle_calculated_sensors_function_minmaxavg(function_sensor):
    """
    Handle the calculated sensors based on the minimum, maximum, or average values.

    Args:
        function_sensor (dict): The configuration for the calculated sensor.
    """

    #print(function_sensor)
    if "sensors" not in function_sensor:
        return
    if "stations" not in function_sensor:
        return
    for sensor in function_sensor["sensors"]:
        #print(sensor)
        values = []

        for station_id in function_sensor["stations"]:
            #print(station_id)

            if sensor == "Pressure":
                station = parse(f"$.devices[?(@._id == '{station_id}')].dashboard_data.Pressure")
            else:
                station = parse(f"$.devices[?(@._id == '{station_id}')].modules[*].dashboard_data.{sensor}")

            for match in station.find(json_netatmo_body):
                if get_dict_value(match.context.context.value, "reachable", "False") != True:
                    break

                dashboard_data = match.context.value
                #print(dashboard_data[sensor])
                values.append(dashboard_data[sensor])
        value = ""
        if values != []:
            if function_sensor["function"] == "min":
                value = min(values)
            elif function_sensor["function"] == "max":
                value = max(values)
            elif function_sensor["function"] == "avg":
                value = avg(values)

        #print(value)
        suffix = ""
        if get_dict_value(function_sensor, "suffix", "") != "":
            suffix = f"_function_sensor['suffix']"
        hass_sensor = f"nfws_{function_sensor['function']}_{sensor}{suffix}"
        hass_sensor_value = {}
        hass_sensor_value["value"] = value

        if "angle" in sensor.lower() and "compass" not in sensor.lower():
            hass_sensor_value["Compass"] = degToCompass(value)
            hass_sensor_value["CompassSymbol"] = degToCompassSymbol(value)

        hass_publish_calculated_station_sensor(hass_sensor, sensor, hass_sensor_value, function_sensor["function"] + suffix)

        if "angle" in sensor.lower() and "compass" not in sensor.lower():
            hass_sensor = f"nfws_{function_sensor['function']}_{sensor}Compass{suffix}"
            hass_sensor_value = {}
            hass_sensor_value["value"] = degToCompass(value)
            hass_publish_calculated_station_sensor(hass_sensor, sensor, hass_sensor_value, function_sensor["function"] + suffix)

            hass_sensor = f"nfws_{function_sensor['function']}_{sensor}CompassSymbol{suffix}"
            hass_sensor_value = {}
            hass_sensor_value["value"] = degToCompassSymbol(value)
            hass_publish_calculated_station_sensor(hass_sensor, sensor, hass_sensor_value, function_sensor["function"] + suffix)

        #print(f"{hass_sensor}: {value}")


def netatmo_handle_calculated_sensors_function_first(function_sensor):
    """
        Handle the calculated sensors based on the minimum, maximum, or average values.

        Args:
            function_sensor (dict): The configuration for the calculated sensor.
    """
    if "sensors" not in function_sensor:
        return
    if "stations" not in function_sensor:
        return
    #print(function_sensor)
    first_sensor = next(iter(function_sensor["sensors"]))
    #print(first_sensor)

    found = False
    for station_id in function_sensor["stations"]:
        #print(station_id)
        station = parse(f"$.devices[?(@._id == '{station_id}')].modules[*].dashboard_data.{first_sensor}")

        for match in station.find(json_netatmo_body):
            station_name = f"{match.context.context.context.context.value['station_name']} in {match.context.context.context.context.value['place']['city']}"
            if get_dict_value(match.context.context.value, "reachable", "False") != True:
                debug_log(f"{station_name}: is not reachable")
                break
            if int(get_dict_value(match.context.value, "WindAngle", "500")) < 0:
                debug_log(f"{station_name}: WindAngle is negative")
                break
            timestampdelta = datetime.timestamp(datetime.now(timezone.utc))-int(get_dict_value(match.context.value, 'time_utc', '500'))
            if timestampdelta>=60*int(get_dict_value(function_sensor, "timeDelta", "30")):
                debug_log(f"{station_name}: last update too long")
                break

            found = True
            dashboard_data = match.context.value
            #print(dashboard_data)

            if first_sensor.lower()[:4] in {"wind", "gust"}:
                dashboard_data["WindAngleCompass"] = degToCompass(dashboard_data["WindAngle"])
                dashboard_data["WindAngleCompassSymbol"] = degToCompassSymbol(dashboard_data["WindAngle"])
                dashboard_data["GustAngleCompass"] = degToCompass(dashboard_data["GustAngle"])
                dashboard_data["GustAngleCompassSymbol"] = degToCompassSymbol(dashboard_data["GustAngle"])

            suffix = ""
            if get_dict_value(function_sensor, "suffix", "") != "":
                suffix = f"_function_sensor['suffix']"
            hass_sensor = f"nfws_{function_sensor['function']}_station_name{suffix}"
            #station_name = f"{match.context.context.context.context.value['station_name']} in {match.context.context.context.context.value['place']['city']}"

            for sensor in function_sensor["sensors"]:
                hass_sensor = f"nfws_{function_sensor['function']}_{sensor}{suffix}"
                if sensor in dashboard_data:
                    hass_sensor_value = {}
                    hass_sensor_value["value"] = f"{dashboard_data[sensor]}"
                    hass_sensor_value["station_name"] = station_name

                    if "angle" in sensor.lower() and "compass" not in sensor.lower():
                        hass_sensor_value["Compass"] = degToCompass(dashboard_data[sensor])
                        hass_sensor_value["CompassSymbol"] = degToCompassSymbol(dashboard_data[sensor])

                    hass_publish_calculated_station_sensor(hass_sensor, sensor, hass_sensor_value, function_sensor["function"] + suffix)
                    #print(f"{hass_sensor}: {hass_sensor_value}")
            break
        if found == True:
            break
        debug_log(f"{station_id}: not found in response")

def netatmo_handle_calculated_sensors():
    """
    Handle the calculated sensors based on the configuration.
    """
    if "calculated_sensors" not in g.config:
        return

    for function_sensor in g.config["calculated_sensors"]:
        if function_sensor["function"] == "first":
            netatmo_handle_calculated_sensors_function_first(function_sensor)
        if function_sensor["function"] in {"min", "max", "avg"}:
            netatmo_handle_calculated_sensors_function_minmaxavg(function_sensor)

def hass_register_sensor_test():
    """
    Registers a sensor in Home Assistant.

    Args:
        entity_name (str): The name of the entity.
        sensor (str): The name of the sensor.
        station (str): The name of the station.

    Returns:
        bool: True if the sensor is successfully registered, False otherwise.
    """

    hass_conf = {}
    hass_conf["unique_id"] = 'nfws_test'
    hass_conf["name"] = 'nfws_test'
    hass_conf["state_topic"] = "nfws/sensor/nfws_test/state"
    hass_conf["json_attributes_topic"] = "nfws/sensor/nfws_test/state" #new
    hass_conf["value_template"] = "{{ value_json.value }}" #new
    # hass_conf["device"] = {
    #     "identifiers": ["Netatmo weather station_70ee50"],
    #     "name": "Netatmo Favourite Weather Stations",
    #     "manufacturer": "Netatmo",
    #     "model": "Weather Stations"
    # }
    # set different device for each station
    hass_conf["device"] = {
        "identifiers": ["nfws_test"],
        "name": "nfws_test",
        "manufacturer": "Netatmo",
        "model": "Weather Stations"
    }

    ret = hass_mqtt_publish("homeassistant/sensor/nfws/nfws_test/config", json.dumps(hass_conf), qos=0, retain=True)
    #print(ret.rc)

    return True