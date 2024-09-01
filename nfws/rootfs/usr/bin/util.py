import global_vars as g
import re
from log import *
from datetime import datetime, timezone

# Precompile the regular expression
sanitize_pattern = re.compile(r'[^a-z0-9]+')

def sanitize_name(name):
    """
    Sanitize a given name by replacing non-alphanumeric characters with underscores,
    converting to lowercase, and removing leading and trailing underscores.

    Args:
        name (str): The name to be sanitized.

    Returns:
        str: The sanitized name.
    """
    return sanitize_pattern.sub('_', name.lower()).strip('_')

def get_dict_value(dictv, key, default = "None"):
    """
    Get the value associated with the given key from the dictionary.
    
    Args:
        dictv (dict): The dictionary to retrieve the value from.
        key: The key to look for in the dictionary.
        default: The default value to return if the key is not found (default is "None").
    
    Returns:
        The value associated with the key if found, otherwise the default value.
    """
    if key in dictv:
        return dictv[key]
    else:
        return default

def debug_log(text):
    """
    Log the given text if the log level is set to "debug".
    
    Args:
        text: The text to log.
    """
    if get_dict_value(g.config["nfws"], "log_level") == "debug":
        logger.debug(snow() + text)

def snow():
    """
    Get the current date and time in the format "dd.mm.yyyy HH:MM:SS".
    
    Returns:
        str: The formatted date and time.
    """
    utc_dt = datetime.now(timezone.utc)
    return utc_dt.astimezone().strftime("%d.%m.%Y %H:%M:%S") + " "

def degToCompass(num):
    """
    Convert a wind direction angle to a compass direction.
    
    Args:
        num (float): The wind direction angle in degrees.
    
    Returns:
        str: The compass direction.
    """
    return degToCompassInternal(num, ["N", "NE", "E", "SE", "S", "SW", "W", "NW"])

def degToCompassSymbol(num):
    """
    Convert a wind direction angle to a compass direction symbol.
    
    Args:
        num (float): The wind direction angle in degrees.
    
    Returns:
        str: The compass direction symbol.
    """
    return degToCompassInternal(num, ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"])

def degToCompassInternal(num, arr):
    """
    Internal function to convert a wind direction angle to a compass direction.
    
    Args:
        num (float): The wind direction angle in degrees.
        arr (list): The list of compass directions.
    
    Returns:
        str: The compass direction.
    """
    val = int((num/45)+.5)
    return arr[(val % 8)]

def avg(lst):
    """
    Calculate the average value of a list.
    
    Args:
        lst (list): The list of values.
    
    Returns:
        float: The average value.
    """
    return round(sum(lst) / len(lst), 1)
