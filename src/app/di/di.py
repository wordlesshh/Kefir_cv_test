class DI(object):

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.add(**kwargs)

    def add(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
