import configparser
import os.path
import string
import typing
from os.path import exists as path_exists
from os.path import isfile as path_isfile
from os.path import dirname
from os import remove, mkdir
import logging


class Configuration:
    SECTIONS = {
        'general': ['check-interval', 'auto-load-certs'],
        'certificates': ['poll-mode', 'locations', 'max-age', 'cert-file', 'message-template'],
        'mail': ['mail-enable', 'sender', 'receiver', 'smtp-server', 'smtp-port', 'smtp-security', 'smtp-user', 'smtp-password']
    }  # section: [list of options]

    DEFAULTS = {
        'check-interval': ('40 6 * * *', str),
        'auto-load-certs': ('True', bool),
        'poll-mode': ('host', str),
        'locations': ('', list),
        'max-age': ('32', int),
        'cert-file': ('cert.pem', str),
        'message-template': ('Certificate of {cert.host} is expiring in {cert.valid_days} days! {nline}It also certifies: {cert.alts}', str),
        'mail-enable': ('False', bool),
        'sender': ('', str),
        'receiver': ('', str),
        'smtp-server': ('', str),
        'smtp-port': ('587', int),
        'smtp-security': ('STARTTLS', str),
        'smtp-user': ('', str),
        'smtp-password': ('', str)
    }  # option: default value

    COMMENTS = {
        'check-interval': """
# Cron expression for the check interval.
# min hour day month day-in-week.
# Default: 40 6 * * * (Check every day at 6:40)""",
        'auto-load-certs': """
# Should the programme automatically load the certificate data?
# Useful for the script polling mode
# Default: True""",
        'poll-mode': """
# Determines what mode to use in general.
# this option can be overridden per location in optional [units]
#
# host: queries certificates online at specified locations to get the currently used certificate
# files: queries certificates from specified directories
# Default: host""",
        'locations': """
# Comma separated list of locations
# If the chosen mode is host, this should be an url. e.g. https://example.org
# If the chosen mode is files, this should be a directory. e.g. /etc/letsencrypt/live/example.org
# To specify a location using custom [certificates] settings, add 'section:' as a prefix to a custom name. e.g. section:example_org
# Default: https://example.org""",
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
# Valid substitutions: 'nline', 'cert.host', 'cert.valid_days', 'cert.valid_seconds', 'cert.valid', 'cert.max-age' & 'cert.alts'
# Default: 'Certificate for {cert.host} is expiring in {cert.valid_days} days!\\nIt certifies: {cert.alts}'""",
        'mail-enable': """
# Enable sending notification via mail?
# Default: False""",
        'sender': """
# Email address to send the mail from.""",
        'receiver': """
# Email address to send the mail to.""",
        'smtp-server': """
# SMTP mail server from when to send the mail.""",
        'smtp-user': """
# SMTP user to send the mail with.""",
        'smtp-password': """
# Password for SMTP user.""",
        'smtp-security': """
# What type of security should be established with the SMTP server?
# PLAIN: no security, TLS, STARTTLS
# Default: STARTTLS"""
    }

    def __init__(self, config_file: string, logger: logging.Logger):
        self.config_file = config_file.replace('~', os.path.expanduser('~'))
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.logger: logging.Logger = logger
        self.config_values = {}

    ##
    # Resets the config file.
    ##
    def reset_config(self):
        if path_exists(self.config_file):
            remove(self.config_file)
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.create_config()

    ##
    # Create the config file from default values.
    ##
    def create_config(self):

        for sec, opts in Configuration.SECTIONS.items():
            self.config.add_section(sec)
            for opt in opts:
                if opt in Configuration.COMMENTS.keys():
                    self.config.set(sec, Configuration.COMMENTS[opt].rstrip())
                self.config.set(sec, opt, Configuration.DEFAULTS[opt][0])

        self.config.set('certificates', """
# It is possible to add a custom section which overrides the options in [certificates].
# It needs to be added in locations. e.g. section:example_org
# You need to specify the same options. e.g.:
# 
# [example_org]
# poll-mode = host
# locations = https://example.org
# max-age = 64""")

        if not path_exists(dirname(self.config_file)):
            mkdir(dirname(self.config_file))

        with open(self.config_file, 'w') as conf:
            self.config.write(conf)

    ##
    # Config reader
    # Returns config values in a dict
    ##
    def read_config(self):
        if not path_exists(self.config_file) or not path_isfile(self.config_file):
            self.logger.warning(f'Config file not found at {self.config_file}, creating from defaults.')
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
                    self.config.set(sec, Configuration.DEFAULTS[opt][0])

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
                for opt in Configuration.SECTIONS['certificates']:
                    if Configuration.DEFAULTS[opt] == '':
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
        value = None
        if fallback is not None and class_type is not bool:
            fallback = class_type(fallback)
        elif fallback is not None:
            fallback = fallback == "True"

        if class_type == str:
            value = self.config.get(section=section, option=option, fallback=None)

        elif class_type == int:
            value = self.config.getint(section=section, option=option, fallback=None)

        elif class_type == float:
            value = self.config.getfloat(section=section, option=option, fallback=None)

        elif class_type == bool:
            value = self.config.getboolean(section=section, option=option, fallback=None)

        elif class_type == list:
            value = self.config.get(section=section, option=option, fallback=None)
            if value is not None:
                value = value.split(',')
                for v in value:
                    i = value.index(v)
                    value[i] = v.strip()


        if value is None and fallback is not None and fallback != '':
            if section in Configuration.SECTIONS.keys():
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


