# https://stackoverflow.com/questions/5022066/how-to-serialize-sqlalchemy-result-to-json
def as_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}
