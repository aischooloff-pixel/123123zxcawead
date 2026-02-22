from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, BigInteger
from database import Base
import datetime

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    balance = Column(Float, default=0.0)

class ProxyOrder(Base):
    __tablename__ = 'proxy_orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    proxy_id = Column(String) 
    ip = Column(String)
    port_http = Column(String)
    port_socks5 = Column(String)
    username = Column(String)
    password = Column(String)
    date_end = Column(DateTime)
    country = Column(String)

class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    invoice_id = Column(Integer, unique=True)
    amount = Column(Float)
    status = Column(String, default='active')
