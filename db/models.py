from sqlalchemy import Column, String, Integer, Numeric, DateTime
from .base import Base
from sqlalchemy import func

class Record(Base):
    __tablename__ = "records"

    LASTUPDATE = Column(Integer, primary_key=True, index=True)
    MARKET = Column(String)
    FROMSYMBOL = Column(String)
    TOSYMBOL = Column(String)
    PRICE = Column(Numeric)
    MEDIAN = Column(Numeric)
    TIMESTAMP = Column(DateTime)
