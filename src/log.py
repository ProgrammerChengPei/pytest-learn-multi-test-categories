# Configure logging

import json5
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('logs/log.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(path: str):
    with open(path, 'r') as f:
        config = json5.load(f)
    return config