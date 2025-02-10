import argparse
import logging
import sys
from argparse import ArgumentParser, Namespace
from pydoc import describe

from cryptography import x509
from cryptography.x509 import DNSName

from configuration import Configuration
from certificate import Certificate
from notification.channel import NotificationChannel
from notification.mail import ChannelMail
from notification.script import ChannelScript


#TODO: rebuild to get all compiled config locations only if config file is modified

class Main:
    def __init__(self, config: str, verbose: bool):
        logging.basicConfig(stream=sys.stdout)
        self.logger: logging.Logger = logging.getLogger("certnotify")

        if verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        self.config: Configuration = Configuration(config, self.logger)
        self.config.read_config()

        self.notifier: NotificationChannel = None

    def setup_channel(self, polling_mode = False):
        if polling_mode:
            self.notifier: NotificationChannel = ChannelScript()
        elif self.config.get('mail-enable'):
            self.notifier: NotificationChannel = ChannelMail(smtp_server=self.config.get('smtp-server'),
                                                             smtp_port=self.config.get('smtp-port'),
                                                             smtp_user=self.config.get('smtp-user'),
                                                             smtp_password=self.config.get('smtp-password'),
                                                             sender=self.config.get('sender'),
                                                             receiver=self.config.get('receiver'))

    def process_location(self, location: str, config_location: str = None):
        self.logger.info(f'Processing location: {location}')
        cert = Certificate(location, self.config, self.logger, config_location)
        self.notifier.register_certificate(cert)

    def process_certificates(self):
        if self.config.get('locations') is None or len(self.config.get('locations')) == 0:
            self.logger.error('No locations configured')
            sys.exit(1)

        for location in self.config.get('locations'):

            if location.startswith('section:'):
                location = location.replace('section:', '')
                if self.config.get('locations', location) is None:
                    self.logger.error(f"No location specified for [{location}]")
                    sys.exit(1)

                sub_locations = self.config.get('locations', location)

                if isinstance(sub_locations, str):
                    self.process_location(location=sub_locations, config_location=location)
                else:
                    for sub_location in sub_locations:
                        self.process_location(location=sub_location, config_location=location)
            else:
                self.process_location(location=location)

    def show_polls(self):
        self.logger.info(", ".join(self.notifier.get_polls()))
        sys.exit(0)

    def finish(self, args: Namespace):
        if isinstance(self.notifier, ChannelScript):
            result = self.notifier.poll(args.poll)
            if len(args.poll) > 1:
                self.logger.info(', '.join(result)) # TODO: incorporate this in .send()?
            else:
                self.logger.info(result)
        elif isinstance(self.notifier, ChannelMail):
            self.notifier.send()

parser = argparse.ArgumentParser('certbot-notify',
                                 description='Python program to check for certificates and notify about expirations.')
parser.add_argument('-c', '--config', default="/etc/certbot-notify.conf", help='Set custom configuration file')
parser.add_argument('-p', '--poll', action='append',
                    help='Specify item to poll, script returns in order of polling. This makes the script run once.')
parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose output')
parser.add_argument('-P', '--print-polls', action='store_true', default=False, help='Print possible items to poll')

if __name__ == "__main__":
    args = parser.parse_args()

    main = Main(config=args.config, verbose=args.verbose)
    main.setup_channel(args.poll or args.print_polls)

    if args.print_polls:
        main.show_polls()
    else:
        main.process_certificates() # TODO: Prevent duplicate cert send
        main.finish(args)