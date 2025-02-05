import argparse
import logging
import sys
from pydoc import describe

from cryptography import x509
from cryptography.x509 import DNSName

from configuration import Configuration
from certificate import Certificate

def process_location(location: str, config: Configuration, logger: logging.Logger, config_location: str = None):
    logger.info(f'Processing location: {location}')
    cert = Certificate(location, config, logger, config_location)
    valid = cert.validate()
    if cert.should_warn(valid):
        logger.warning(f"{cert.location} expires in just {valid.days} days!")
    logger.debug(f"{cert.location} expires in {valid.days} days")
    logger.info(f"Cert is valid for {', '.join(cert.get_hosts())}")


def process_certificates(config: Configuration, logger: logging.Logger):
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

def init(config: str, verbose: bool):
    logging.basicConfig(stream=sys.stdout)
    logger = logging.getLogger("certbot-notify")

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    config = Configuration(config, logger)
    config.read_config()
    return config, logger

def define_parser():
    parser = argparse.ArgumentParser('certbot-notify', description='Python program to check for certificates and notify about expirations.')
    parser.add_argument('-c', '--config', default="/etc/certbot-notify.conf")
    parser.add_argument('-p', '--poll', action='append')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)

    return parser

if __name__ == "__main__":

    parser = define_parser()
    args = parser.parse_args()

    config, logger = init(config=args.config, verbose=args.verbose)
    process_certificates(config, logger)
