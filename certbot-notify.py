import configuration, certificate
from certificate import Certificate

certificates = []

def summon_cert(location, check_interval, max_age, mode):
    cert = Certificate(location=location, check_interval=check_interval, max_age=max_age, mode=mode)
    certificates.append(cert)

def process_location(config, location):
    summon_cert(location=location, check_interval=config['check-interval'],
                max_age=config['max-age'], mode=config['mode'])

if __name__ == "__main__":
    config = configuration.read_config()

    for location in config['locations']:

        if location.startswith('section:'):
            location = location.replace('section:', '')
            for sub_location in config[location]['locations']:
                process_location(config[location], sub_location)
        else:
            process_location(config, location)


