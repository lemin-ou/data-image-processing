from asyncio.log import logger
from stat import filemode
import sys
import logging
from datetime import datetime


# get logger
logging.basicConfig(handlers=[
    logging.FileHandler("log-%s.log" %
                        datetime.now(tz=None).replace(microsecond=0, second=0, minute=0).isoformat()),
    logging.StreamHandler(sys.stdout)
],  format='%(asctime)s#%(levelname)s#%(filename)s#%(funcName)s#%(lineno)d: %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
