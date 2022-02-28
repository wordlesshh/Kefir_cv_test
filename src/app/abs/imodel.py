from .idi import IDi


class IModel(IDi):

    def __init__(self, di, db=None) -> None:
        super().__init__(di)

        if db is not None:
            self._db = db
        else:
            self._db = di.db

    @property
    def db(self):
        return self._db

    def set_db(self, db):
        self._db = db
