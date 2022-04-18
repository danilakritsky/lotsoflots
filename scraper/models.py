from scrapy.utils.project import get_project_settings

from sqlalchemy import create_engine, Column, Table, ForeignKey, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Integer, String, Date, DateTime, Float, Boolean, Text)
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.url import URL



SETTINGS = get_project_settings()

DeclarativeBase = declarative_base()

def db_connect() -> Engine:
    """Connect to a postgres instance."""
    return create_engine(URL(**SETTINGS.get("POSTGRES")))

def create_lots_table(engine: Engine):
    """Create the lots table"""
    DeclarativeBase.metadata.create_all(engine)


class Lots(DeclarativeBase):
    """Representation of a table that stores information on lots."""

    __tablename__ = "lots"
    
    id = Column(Integer, primary_key=True)
    auction = Column('auction', String)
    auction_num = Column('auction_num', Integer)
    lot_num = Column('lot_num', Integer)
    lot_artist = Column('lot_artist', String)
    lot_title = Column('lot_title', String)
    lot_dimensions = Column('lot_dimensions', String)
    lot_image_url = Column('lot_image_url', String)