import logging
import sys

from cryptography import x509
from cryptography.x509 import DNSName

from configuration import Configuration
from certificate import Certificate

certificates = []


def process_location(location: str, config: Configuration, logger: logging.Logger, config_location: str = None):
    logger.info(f'Processing location: {location}')
    cert = Certificate(location, config, logger, config_location)
    certificates.append(cert)
    valid = cert.validate()
    if cert.should_warn(valid):
        logger.warning(f"{cert.location} expires in just {valid.days} days!")
    logger.debug(f"{cert.location} expires in {valid.days} days")
    logger.info(f"Cert is valid for {', '.join(cert.get_hosts())}")


def main():
    logging.basicConfig(stream=sys.stdout)
    logger = logging.getLogger("certbot-notify")

    logger.setLevel(logging.DEBUG)

    config = Configuration('./test/certbot-notify.conf', logger)
    config.read_config()

    if config.get('locations') is None or len(config.get('locations')) == 0:
        logger.error('No locations configured')
        sys.exit(1)

    for location in config.get('locations'):

        if location.startswith('section:'):
            location = location.replace('section:', '')
            for sub_location in config.get('locations', location):
                process_location(sub_location, config, logger)
        else:
            process_location(location, config, logger)


if __name__ == "__main__":
    main()
