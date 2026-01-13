import logging 
from pathlib import Path 

def pytest_configure(config):
    Path("log").mkdir(exist_ok = True)

    handlers = [
        logging.StreamHandler(),
        logging.FileHandler("logs/pytest.log", encoding = 'utf-8-sig')
    ]

    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers = handlers,
        force = True
    )
    