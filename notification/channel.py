import typing
from abc import ABC, abstractmethod

from certificate import Certificate


class NotificationChannel(ABC):

    def __init__(self):
        self.certificates: typing.Dict[str, Certificate] = {}

    ##
    # Send message to notification channel
    ##
    @abstractmethod
    def send(self):
        pass

    ##
    # Poll for data
    ##
    @abstractmethod
    def poll(self, param: str) -> int | str:
        pass

    ##
    # Get possible items to poll
    ##
    @abstractmethod
    def get_polls(self):
        pass

    def register_certificate(self, cert: Certificate):
        self.certificates[cert.location.replace('.', '_')] = cert

    def get_certificate(self, ident: str) -> Certificate:
        return self.certificates[ident] if ident in self.certificates.keys() else None
