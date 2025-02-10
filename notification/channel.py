import logging
import typing
from abc import ABC, abstractmethod

from certificate import Certificate


class NotificationChannel(ABC):

    def __init__(self, logger: logging.Logger):
        self.certificates: typing.Dict[str, Certificate] = {}
        self.logger: logging.Logger = logger

    ##
    # Send message to notification channel
    ##
    @abstractmethod
    def send(self, params: typing.List[str] = None) -> typing.Any:
        pass

    def register_certificate(self, cert: Certificate):
        self.certificates[cert.location.replace('.', '_')] = cert

    def get_certificate(self, ident: str) -> Certificate:
        return self.certificates[ident] if ident in self.certificates.keys() else None
