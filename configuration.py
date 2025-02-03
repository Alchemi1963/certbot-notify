import configparser
from os.path import exists as path_exists
from os.path import isfile as path_isfile
from os import remove

CONFIG_FILE = "./test/certbot_notify.conf"

SECTIONS = {
    'general': ['mode', 'locations', 'check-interval', 'max-age', 'cert-file']
} # section: [list of options]
DEFAULTS = {
    'mode': 'host',
    'locations': '',
    'check-interval': 24,
    'max-age': 32,
    'cert-file': 'cert.pem'
} # option: default value
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
# To specify a location using custom settings, add 'section:' as a prefix to a custom name. e.g. section:example_org
# Default: https://example.org
""",
    'check-interval': """
# How often should the certificates be checked in hours.
# Default: 24
""",
    'max-age': """
# The amount of time in days before warnings about certificate expiry should be issued.
# Default: 32
""",
    'cert-file': """
# Comma separated list of filename(s) to check. e.g. cert.pem, fullchain.pem.
# This option only applies if files mode is chosen.
# Note: other certificate files might cause inaccuracies.
# Default: cert.pem
"""
}

##
# Resets the config file.
##
def reset_config():
    if path_exists(CONFIG_FILE):
        remove(CONFIG_FILE)
    create_config()

##
# Create the config file from default values.
##
def create_config():
    config = configparser.ConfigParser(allow_no_value=True)

    for sec, opts in SECTIONS.items():
        config.add_section(sec)
        for opt in opts:
            if opt in COMMENTS.keys():
                config.set(sec, COMMENTS[opt])
            config.set(sec, opt, DEFAULTS[opt])
        config.set(sec, """
# It is possible to add a custom section which overrides the options in [general].
# It needs to be added in locations. e.g. section:example_org
# You need to specify the same options. e.g.:
# 
# [example_org]
# mode = host
# locations = https://example.org,https://jellyfin.example.org
# check-interval = 64
""")

    with open(CONFIG_FILE, 'w') as conf:
        config.write(conf)

##
# Option value getter which returns in the correct variable type
# Returns option value or fallback
##
def get_option(config, section, option, fallback = None):
    try:
        value = config.get(section, option, fallback = fallback)
        if ',' in value:
            value = value.split(',')
    except TypeError:
        try:
            value = config.getint(section, option, fallback = fallback)
        except TypeError:
            try:
                value = config.getfloat(section, option, fallback = fallback)
            except TypeError:
                value = config.getboolean(section, option, fallback = fallback)
    #log if value equals fallback
    return value

##
# Main config reader, only searches for the default section(s).
# Returns config values in a dict
##
def read_config():
    if not path_exists(CONFIG_FILE) or not path_isfile(CONFIG_FILE):
        create_config()

    config = configparser.ConfigParser()

    config.read(CONFIG_FILE)

    config_values = {}

    for sec, opts in SECTIONS.items():
        if not config.has_section(sec):
            #log section not present, adding
            config.add_section(sec)
            for opt in opts:
                config.set(sec, DEFAULTS[opt])

        for opt in opts:
            config_values[opt] = get_option(config, sec, opt, DEFAULTS[opt])

    return config_values

##
# Extra config reader, only searches for the custom section(s).
# Returns extra config values in a dict
##
def read_config_extra(config_values):
    if not path_exists(CONFIG_FILE) or not path_isfile(CONFIG_FILE):
        create_config()

    config = configparser.ConfigParser()

    config.read(CONFIG_FILE)

    config_values_extra = {}

    if len(config.sections()) > 1:
        for sec in config.sections():
            if sec in SECTIONS.keys():
                continue
            section = {}
            for opt in DEFAULTS.keys():
                section[opt] = get_option(config, sec, opt, config_values[opt])
            config_values_extra[sec] = section
    return config_values_extra