import argparse
import logging
import sys
from pydoc import describe

from cryptography import x509
from cryptography.x509 import DNSName

from configuration import Configuration
from certificate import Certificate
from notification.channel import NotificationChannel
from notification.mail import ChannelMail
from notification.script import ChannelScript


#TODO: rebuild as class
#TODO: rebuild to get all compiled config locations only if config file is modified

def process_location(notifier: NotificationChannel, location: str, config: Configuration, logger: logging.Logger,
                     config_location: str = None):
    logger.info(f'Processing location: {location}')
    cert = Certificate(location, config, logger, config_location)
    notifier.register_certificate(cert)


def process_certificates(config: Configuration, logger: logging.Logger, notifier: NotificationChannel):
    if config.get('locations') is None or len(config.get('locations')) == 0:
        logger.error('No locations configured')
        sys.exit(1)

    for location in config.get('locations'):

        if location.startswith('section:'):
            location = location.replace('section:', '')
            if config.get('locations', location) is None:
                logger.error(f"No location specified for [{location}]")
                sys.exit(1)

            sub_locations = config.get('locations', location)

            if isinstance(sub_locations, str):
                process_location(location=sub_locations, config=config, logger=logger, config_location=location,
                                 notifier=notifier)
            else:
                for sub_location in sub_locations:
                    process_location(location=sub_location, config=config, logger=logger, config_location=location,
                                     notifier=notifier)
        else:
            process_location(location=location, config=config, logger=logger, notifier=notifier)


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
    parser = argparse.ArgumentParser('certbot-notify',
                                     description='Python program to check for certificates and notify about expirations.')
    parser.add_argument('-c', '--config', default="/etc/certbot-notify.conf", help='Set custom configuration file')
    parser.add_argument('-p', '--poll', action='append',
                        help='Specify item to poll, script returns in order of polling. This makes the script run once.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose output')
    parser.add_argument('-P', '--print-polls', action='store_true', default=False, help='Print possible items to poll')

    return parser


def show_polls(notifier: NotificationChannel):
    logger.info(", ".join(notifier.get_polls()))
    sys.exit(0)


if __name__ == "__main__":
    parser = define_parser()
    args = parser.parse_args()
    notifier: NotificationChannel = None

    config, logger = init(config=args.config, verbose=args.verbose)

    logger.debug(config.get('smtp-port'))

    if args.poll or args.print_polls:
        notifier = ChannelScript()
        if args.print_polls:
            show_polls(notifier)
    elif config.get('mail-enable'):
        notifier = ChannelMail(smtp_server=config.get('smtp-server'),
                               smtp_port=config.get('smtp-port'),
                               smtp_user=config.get('smtp-user'),
                               smtp_password=config.get('smtp-password'),
                               sender=config.get('sender'),
                               receiver=config.get('receiver'))

    process_certificates(config, logger, notifier)

    if args.poll:
        poll_result = notifier.poll(args.poll)
        try:
            logger.info(', '.join(poll_result))
        except TypeError:
            logger.info(poll_result)
    elif config.get('mail-enable'):
        notifier.send()