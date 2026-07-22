from sqlalchemy import Column, String, Text
from app.db.base_class import Base

class SystemSetting(Base):
    """
    Modèle pour stocker des configurations globales du système (clé/valeur).
    Les valeurs sensibles peuvent être chiffrées avant stockage.
    """
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True, index=True)
    value = Column(Text, nullable=False)
