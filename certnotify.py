import logging
import sys
from argparse import ArgumentParser

from configuration import Configuration
from certificate import Certificate
from notification.channel import NotificationChannel
from notification.mail import ChannelMail
from notification.script import ChannelScript


class Main:
    def __init__(self, config: str, level: str):
        logging.basicConfig(stream=sys.stdout)
        self.logger: logging.Logger = logging.getLogger("certnotify")

        self.logger.setLevel(logging.getLevelNamesMapping()[level.upper()])

        self.config: Configuration = Configuration(config, self.logger)
        self.config.read_config()

        self.notifier: NotificationChannel = None

    def setup_channel(self, polling_mode = False):
        if polling_mode:
            self.notifier: NotificationChannel = ChannelScript(self.logger)
        elif self.config.get('mail-enable'):
            self.notifier: NotificationChannel = ChannelMail(logger= self.logger,
                                                             smtp_server=self.config.get('smtp-server'),
                                                             smtp_port=self.config.get('smtp-port'),
                                                             smtp_security=self.config.get('smtp-security'),
                                                             smtp_user=self.config.get('smtp-user'),
                                                             smtp_password=self.config.get('smtp-password'),
                                                             sender=self.config.get('sender'),
                                                             receiver=self.config.get('receiver'))

    def get_certificate(self, location: str, config_location: str = None):
        self.logger.info(f'Processing location: {location}')
        cert = Certificate(location, self.config, self.logger, config_location)
        self.notifier.register_certificate(cert)

        if self.config.get('auto-load-certs'):
            cert.load_cert_data()

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

                for sub_location in self.config.get('locations', location):
                    self.get_certificate(location=sub_location, config_location=location)

            else:
                self.get_certificate(location=location)

    def show_polls(self):
        self.logger.info(self.notifier.send(['polls']))
        sys.exit(0)

    def finish(self):

        if isinstance(self.notifier, ChannelScript):
            result = self.notifier.send(args.poll)
            self.logger.info(result)

        elif isinstance(self.notifier, ChannelMail):
            self.notifier.send()

parser = ArgumentParser('certbot-notify',
                                 description='Python program to check for certificates and notify about expirations.')
parser.add_argument('-c', '--config', default="/etc/certbot-notify.conf", help='Set custom configuration file')
parser.add_argument('-p', '--poll', action='append',
                    help='Specify item to poll, script returns in order of polling. This makes the script run once.')
parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose output, equal to: --log-level DEBUG')
parser.add_argument('-P', '--print-polls', action='store_true', default=False, help='Print possible items to poll')
parser.add_argument('-l', '--log-level', default='INFO', help='Define log level. Choose from DEBUG, INFO, WARN, ERROR, FATAL, CRITICAL')

if __name__ == "__main__":
    args = parser.parse_args()

    if args.verbose:
        args.log_level = 'DEBUG'

    main = Main(config=args.config, level=args.log_level)
    main.setup_channel(args.poll or args.print_polls)

    if args.print_polls:
        main.show_polls()
    else:
        main.process_certificates()
        main.finish()