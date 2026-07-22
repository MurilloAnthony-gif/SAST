from app.extensions import db


class Sector(db.Model):
    __tablename__ = 'sectores'

    id_sector = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_sector = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Sector {self.nombre_sector}>'
