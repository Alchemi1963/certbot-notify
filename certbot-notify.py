import logging

from configuration import Configuration
from certificate import Certificate

certificates = []


def process_location(location: str, config: Configuration, logger: logging.Logger, config_location: str = None):
    logger.info(f'Processing location: {location}')
    cert = Certificate(location, config, logger, config_location)
    certificates.append(cert)


if __name__ == "__main__":
    logger = logging.getLogger("certbot-notify")
    config = Configuration('./test/certbot-notify.conf', logger)
    config.read_config()

    for location in config.get('locations'):

        if location.startswith('section:'):
            location = location.replace('section:', '')
            for sub_location in config.get('locations', location):
                process_location(sub_location, config, logger)
        else:
            process_location(location, config, logger)

