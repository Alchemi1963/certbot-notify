import sys
from abc import ABC

from email.message import EmailMessage
from smtplib import SMTPNotSupportedError

from notification.channel import NotificationChannel
import smtplib

class ChannelMail(NotificationChannel, ABC):
    def __init__(self, smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str, sender: str,
                 receiver: str):
        super().__init__()
        self.sender: str = sender
        self.receiver: str = receiver
        self.smtp_server: smtplib.SMTP = smtplib.SMTP(host=smtp_server, port=smtp_port)
        self.smtp_server.user = smtp_user
        self.smtp_server.password = smtp_password
        try:
            print(self.smtp_server.starttls())
            print(self.smtp_server.auth('plain', self.smtp_server.auth_plain))
        except SMTPNotSupportedError:
            sys.exit(1)

    def send(self):
        for cert in self.certificates.values():
            cert.until_expiry()
            if cert.should_warn():
                msg = EmailMessage()
                msg.set_content(cert.get_message())
                msg['Subject'] = 'Certificate expiry'
                msg['From'] = self.sender
                msg['To'] = self.receiver
                self.smtp_server.send_message(msg)

    def poll(self, param: str) -> int | str:
        pass

    def get_polls(self):
        pass
