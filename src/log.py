# Configure logging

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(name)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('log/log.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
