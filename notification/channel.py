from abc import ABC, abstractmethod

from certificate import Certificate


class NotificationChannel(ABC):
    def __init__(self):
        pass

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