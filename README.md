# Certnotify 
## A programme which polls certificates and notifies you when it's getting old

Certnotify can poll a certificate by it's file or by downloading it from the host, as specified in the config file.
You can specify the `max-age` per certificate, as well as the `poll-mode` and the `message-template` by adding a new `[section]` in the config and specifying it in `locations`.

## Installation
### --- Debian based systems ---
1. Download the latest release and install it with `dpkg -i certnotiy.deb`
2. Configure the programme. By default the config file will be in `~/.config/certnotify.conf`. This can be changed by command-line argument.
3. (Optional) to install it in `/etc/cron.d/` run it with the `-i` option, to install it with the current configuration file, specify `-I` as well.

### --- Other systems ---
1. Clone the git repo in your desired directory
2. Create a python3 virtual environment in `<install_dir>/venv` and install `cryptography` <br> (`cd <install_dir> && python3 -m venv venv && pip install cryptography`)
4. Run the programme once. Either with `usr/bin/certnotify` or invoking it directly `python3 certnotify.py`. Note: you need the `cryptography` pip package!
5. Configure the programme. By default the config file will be in `~/.config/certnotify.conf`. This can be changed by command-line argument.
6. (Optional) to install it in `/etc/cron.d/` run it with the `-i` option, to install it with the current configuration file, specify `-I` as well.

## Command line arguments:
| option               | description                                              | default value               |
|----------------------|----------------------------------------------------------|-----------------------------|
| -c, --config         | set custom configuration file                            | `~/.config/certnotify.conf` |
| -p, --poll           | poll specific item(s). can be used multiple times        |                             |
| -P, --print-polls    | print possible items to poll for use with `--poll`       |                             |
| -i, --install        | install cronjob into `/etc/cron.d/`                      |                             |
| -I, --install-config | install cronjob with config file used in `--config`      |                             |
| -u, --uninstall      | uninstall cronjob                                        |                             |
| -v, --verbose        | set log level to `DEBUG`                                 |                             |
| -l, --log-level      | define log level                                         | INFO                        |
| --reset              | reset configuration file to defaults                     |                             |
| --cron               | run in cron mode, this outputs to `/var/log/certnotify/` |                             |

## Contributing
To contribute to this repo, follow the installation instructions for other systems up until step 2.
I recommend creating a `test` directory to store your config file and other needed files.

### Building .deb
Run `sudo bash build.sh`, it will create a .deb file.<br>(`sudo` is needed to make `root:root` the owner of the temporary files for the .deb package to play nice at installation time)

Note: `build.sh` was made on an ArchLinux system, it may behave differently on other systems, proceed with care.
