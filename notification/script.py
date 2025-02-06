import typing
from abc import ABC

from notification.channel import NotificationChannel


class ChannelScript(NotificationChannel, ABC):
    polls = ['certs', 'cert.<id>.valid_days', 'cert.<id>.valid_seconds', 'cert.<id>.valid', 'cert.<id>.max-age', 'cert.<id>.should_warn']

    def send(self):
        pass

    def poll(self, params: typing.List[str]) -> int | float | str | None:
        for p in params:
            cert = None
            if '.' in p:
                c, ident, l = p.split('.')
                p = f'{c}.<id>.{l}'
                cert = self.get_certificate(ident)
                if cert is None:
                    return None
            if p not in self.polls:
                return None

            match self.polls.index(p):
                case 0:
                    return self.certificates.keys()
                case 1:
                    return cert.until_expiry().days
                case 2:
                    return cert.until_expiry().total_seconds()
                case 3:
                    return cert.validate()
                case 4:
                    return cert.max_age
                case 5:
                    return cert.should_warn(cert.until_expiry())

    def get_polls(self):
        return self.polls
