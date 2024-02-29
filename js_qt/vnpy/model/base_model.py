from peewee import *

from vnpy.trader.database import database_manager

db = database_manager.db


class BaseModel(Model):
    class Meta:
        database = db
