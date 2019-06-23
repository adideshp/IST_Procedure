import abc

class Algorithm:
    def __init__(self, strategy):
        self._strategy = strategy

    def execute(self):
        self._strategy.execute()


class Strategy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def execute():
        pass