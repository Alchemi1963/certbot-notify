import datetime
import logging
import os
import sys
from argparse import ArgumentParser

from configuration import Configuration
from certificate import Certificate
from notification.channel import NotificationChannel
from notification.mail import ChannelMail
from notification.script import ChannelScript


class Main:
    def __init__(self, config: str, level: str, cron: bool):

        handler = logging.StreamHandler(stream=sys.stdout)
        if cron:
            if not os.path.exists('/var/log/certnotify'):
                os.mkdir('/var/log/certnotify')

            now = datetime.datetime.now()
            handler = logging.FileHandler(filename=f'/var/log/certnotify/{now.strftime("%d-%m-%Y_%H-%M-%S")}.log')

        logging.basicConfig(
            level=logging.getLevelNamesMapping()[level.upper()],
            handlers=[handler],
            format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
        )

        self.logger: logging.Logger = logging.getLogger("certnotify")

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

        if ((self.config.get('locations')[0] == '' and len(self.config.get('locations')) == 1)
                or len(self.config.get('locations')) == 0):
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

    def install_cron(self):
        self.test_root()
        cron_file = '/etc/cron.d/certnotify'
        conf_file = os.path.realpath(self.config.config_file) if args.install_config else "~/.config/certnotify.conf"
        with open(cron_file, 'wt') as cron:
            cron.write(f"""# certnotify cron job
SHELL=/bin/bash
PATH={os.path.join(os.path.dirname(os.path.realpath(__file__)), 'venv', 'bin')}
{self.config.get('check-interval')} root python3 \"{os.path.realpath(__file__)}\" --cron --config \"{conf_file}\"
""")

        sys.exit(0)

    def uninstall_cron(self):
        self.test_root()
        os.remove('/etc/cron.d/certnotify')

        sys.exit(0)

    def reset(self):
        self.config.reset_config()
        sys.exit(0)

    def test_root(self):
        if os.geteuid() != 0:
            self.logger.error('Running without root permissions, unable to complete task.')
            sys.exit("You need root permissions to do this, please run script as root.")

    def finish(self):

        if isinstance(self.notifier, ChannelScript):
            result = self.notifier.send(args.poll)
            self.logger.info(result)

        elif isinstance(self.notifier, ChannelMail):
            self.notifier.send()

parser = ArgumentParser('certnotify',
                                 description='Python program to check for certificates and notify about expirations.')
parser.add_argument('-c', '--config', default="~/.config/certnotify.conf", help='Set custom configuration file')
parser.add_argument('-p', '--poll', action='append',
                    help='Specify item to poll, script returns in order of polling. This makes the script run once.')
parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose output, equal to: --log-level DEBUG')
parser.add_argument('-P', '--print-polls', action='store_true', default=False, help='Print possible items to poll')
parser.add_argument('-l', '--log-level', default='INFO', help='Define log level. Choose from DEBUG, INFO, WARN, ERROR, FATAL, CRITICAL')
parser.add_argument('-i', '--install', action='store_true', help='Install script into /etc/cron.d using default arguments')
parser.add_argument('-I', '--install-config', action='store_true', help='Install cron with specified config file')
parser.add_argument('-u', '--uninstall', action='store_true', help='Uninstall cron job')
parser.add_argument('--reset', action='store_true', help='Reset default configuration')
parser.add_argument('--cron', action='store_true', help='Run in cron mode')

if __name__ == "__main__":
    args = parser.parse_args()

    if args.verbose:
        log_level = 'DEBUG'
    else:
        log_level = args.log_level

    main = Main(config=args.config, level=log_level, cron=args.cron)

    if args.install:
        main.install_cron()
    elif args.uninstall:
        main.uninstall_cron()
    elif args.reset:
        main.reset()

    main.setup_channel(args.poll or args.print_polls)

    if args.print_polls:
        main.show_polls()
    else:
        main.process_certificates()
        main.finish()