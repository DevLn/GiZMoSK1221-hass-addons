import logging
from datetime import datetime, timezone

logging.basicConfig(format='%(message)s')  #DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger('nfws')
logger.setLevel('DEBUG')
logger.info("-------------------------------------------------------------------------------------------------------------")
logger.info(datetime.now(timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M:%S") + " Starting Netatmo service")
