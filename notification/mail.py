import logging
import sys
import typing
from abc import ABC

from email.message import EmailMessage
from smtplib import SMTPNotSupportedError, SMTPAuthenticationError, SMTPException

from notification.channel import NotificationChannel
import smtplib

class ChannelMail(NotificationChannel, ABC):
    def __init__(self, logger: logging.Logger, smtp_server: str, smtp_port: int, smtp_security: str, smtp_user: str, smtp_password: str, sender: str,
                 receiver: str):
        super().__init__(logger)

        if not all([smtp_server, smtp_port, smtp_user, smtp_password, sender, receiver]):
            self.logger.error("No SMTP server properly configured. Exiting.")
            sys.exit(1)

        self.sender: str = sender
        self.receiver: str = receiver

        match smtp_security.upper():
            case "STARTTLS":
                self.smtp_server: smtplib.SMTP = smtplib.SMTP(host=smtp_server, port=smtp_port)
                self.__debuglog_command(self.smtp_server.starttls())
            case "TLS":
                self.smtp_server: smtplib.SMTP = smtplib.SMTP_SSL(host=smtp_server, port=smtp_port)
            case "PLAIN":
                self.smtp_server: smtplib.SMTP = smtplib.SMTP(host=smtp_server, port=smtp_port)
            case _:
                self.smtp_server: smtplib.SMTP = smtplib.SMTP(host=smtp_server, port=smtp_port)

        try:
            self.__debuglog_command(self.smtp_server.login(smtp_user, smtp_password))
        except SMTPNotSupportedError:
            self.logger.error('SMTP server does not support AUTH command.')
            sys.exit(1)
        except SMTPAuthenticationError:
            self.logger.error('Provided user/password combination invalid for SMTP server.')
            sys.exit(1)
        except SMTPException:
            self.logger.error('No suitable authentication method was found for the SMTP server.')
            sys.exit(1)

    def send(self, params: typing.List[str] = None) -> typing.Any:
        self.prune_certificates()

        for cert in self.certificates.values():
            if cert.data is None:
                cert.load_cert_data()

            if cert.should_warn():
                msg = EmailMessage()
                msg.set_content(cert.get_message())
                msg['Subject'] = 'Certificate expiry'
                msg['From'] = self.sender
                msg['To'] = self.receiver
                self.smtp_server.send_message(msg)
                self.logger.info(f'Send mail to {self.receiver}')

    def __debuglog_command(self, command: typing.Tuple[int, bytes]):
        self.logger.debug(f'Code {str(command[0])} - {command[1].decode()}')