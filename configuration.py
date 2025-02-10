import configparser
import string
import typing
from os.path import exists as path_exists
from os.path import isfile as path_isfile
from os import remove
import logging


class Configuration:
    SECTIONS = {
        'general': ['check-interval'],
        'certificates': ['poll-mode', 'locations', 'max-age', 'cert-file', 'message-template'],
        'mail': ['mail-enable', 'sender', 'receiver', 'smtp-server', 'smtp-port', 'smtp-user', 'smtp-password']
    }  # section: [list of options]

    DEFAULTS = {
        'mode': ('host', str.__class__),
        'locations': (None, typing.List.__class__),
        'check-interval': ('24', int.__class__),
        'max-age': ('32', int.__class__),
        'cert-file': ('cert.pem', str.__class__),
        'message-template': ('Certificate for {cert.host} is expiring in {cert.valid_days} days! {nline}It also certifies: {cert.alts}', str.__class__),
        'mail-enable': ('True', bool.__class__),
        'sender': ('', str.__class__),
        'receiver': ('', str.__class__),
        'smtp-server': ('', str.__class__),
        'smtp-port': ('587', int.__class__),
        'smtp-user': ('', str.__class__),
        'smtp-password': ('', str.__class__)
    }  # option: default value

    COMMENTS = {
        'mode': """
# Determines what mode to use in general.
# this option can be overridden per location in optional [units]
#
# host: queries certificates online at specified locations to get the currently used certificate
# file: queries certificates from specified directories
# Default: host""",
        'locations': """
# Comma separated list of locations
# If the chosen mode is host, this should be an url. e.g. https://example.org
# If the chosen mode is files, this should be a directory. e.g. /etc/letsencrypt/live/example.org
# To specify a location using custom [general] settings, add 'section:' as a prefix to a custom name. e.g. section:example_org
# Default: https://example.org""",
        'check-interval': """
# How often should the certificates be checked in hours.
# Default: 24""",
        'max-age': """
# The amount of time in days before warnings about certificate expiry should be issued.
# Default: 32""",
        'cert-file': """
# Certificate file to check. e.g. cert.pem, fullchain.pem.
# This option only applies if files mode is chosen.
# Note: other certificate files might cause inaccuracies.
# Default: cert.pem""",
        'message-template': """
# Message template.
# Use {} for substitutions.
# Valid substitions: 'nline', 'cert.host', 'cert.valid_days', 'cert.valid_seconds', 'cert.valid', 'cert.max-age' & 'cert.alts'
# Default: 'Certificate for {cert.host} is expiring in {cert.valid_days} days!\\nIt also certifies: {cert.alts}'""",
        'mail-enable': """
# Enable sending notification via mail?
# Default: True""",
        'sender': """
# Email address to send the mail from.""",
        'receiver': """
# Email address to send the mail to.""",
        'smtp-server': """
# SMTP mail server from when to send the mail.""",
        'smtp-user': """
# SMTP user to send the mail with.""",
        'smtp-password': """
# Password for SMTP user."""
    }

    def __init__(self, config_file: string, logger: logging.Logger):
        self.config_file = config_file
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.logger: logging.Logger = logger
        self.config_values = {}

    ##
    # Resets the config file.
    ##
    def reset_config(self):
        if path_exists(self.config_file):
            remove(self.config_file)
        self.create_config()

    ##
    # Create the config file from default values.
    ##
    def create_config(self):
        for sec, opts in Configuration.SECTIONS.items():
            self.config.add_section(sec)
            for opt in opts:
                if opt in Configuration.COMMENTS.keys():
                    self.config.set(sec, Configuration.COMMENTS[opt])
                self.config.set(sec, opt, Configuration.DEFAULTS[opt])
            self.config.set(sec, """
# It is possible to add a custom section which overrides the options in [general].
# It needs to be added in locations. e.g. section:example_org
# You need to specify the same options. e.g.:
# 
# [example_org]
# mode = host
# locations = https://example.org,https://jellyfin.example.org
# check-interval = 64
""")

        with open(self.config_file, 'w') as conf:
            self.config.write(conf)

    ##
    # Config reader
    # Returns config values in a dict
    ##
    def read_config(self):
        if not path_exists(self.config_file) or not path_isfile(self.config_file):
            self.create_config()

        self.config.read(self.config_file)

        self.__get_sections()
        self.__get_extra_sections()

        return self.config_values

    def __get_sections(self):
        for sec, opts in Configuration.SECTIONS.items():
            if not self.config.has_section(sec):
                self.logger.warning(f"Section '{sec}' not found in {self.config_file}, adding default values.")
                self.config.add_section(sec)
                for opt in opts:
                    self.config.set(sec, Configuration.DEFAULTS[opt])

            for opt in opts:
                self.config_values[opt] = self.__get_option(section=sec, option=opt, fallback=Configuration.DEFAULTS[opt][0], class_type=Configuration.DEFAULTS[opt][1])

    def __get_extra_sections(self):
        # Get the extra custom values
        if len(self.config.sections()) > len(Configuration.SECTIONS):
            for sec in self.config.sections():
                if sec in Configuration.SECTIONS.keys():
                    continue
                self.logger.info(f"Section '{sec}' found.")
                section = {}
                for opt in Configuration.DEFAULTS.keys():
                    if Configuration.DEFAULTS[opt] is None:
                        section[opt] = self.__get_option(section=sec, option=opt, fallback=None, class_type=Configuration.DEFAULTS[opt][1])
                    else:
                        section[opt] = self.__get_option(section=sec, option=opt, fallback=self.config_values[opt], class_type=Configuration.DEFAULTS[opt][1])
                    self.logger.debug(f"Option '{opt}' set to '{section[opt]}'.")
                self.config_values[sec] = section

    ##
    # Option value getter which returns in the correct variable type
    # Returns option value or fallback
    ##
    def __get_option(self, section, option, fallback=None, class_type=None):
        match class_type:
            case str.__class__:
                value = self.config.get(section=section, option=option, fallback=None)
            case int.__class__:
                value = self.config.getint(section=section, option=option, fallback=None)
            case float.__class__:
                value = self.config.getfloat(section=section, option=option, fallback=None)
            case bool.__class__:
                value = self.config.getboolean(section=section, option=option, fallback=None)
            case typing.List.__class__:
                value = self.config.get(section=section, option=option, fallback=None).split(',')
            case _:
                value = None

        if value is None:
            self.logger.info(f"Value for '{option}' in [{section}] not found, falling back to '{fallback}'.")
            value = fallback

        return value

    ##
    # Getter help function for configuration values
    ##
    def get(self, option: str, location = None) -> str | int | float | typing.List[str] | bool:
        if location is not None:
            return self.config_values.get(location).get(option)
        return self.config_values.get(option) if option in self.config_values else None


