from abc import ABC

import channel

class ChannelScript(channel.NotificationChannel, ABC):
    def send(self):
        pass

    def poll(self, param: str) -> int | str:
        pass

