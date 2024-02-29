from peewee import MySQLDatabase

settings = {
    'host': '192.168.0.250',
    'user': 'stock',
    'password': '123456',
    'port': 3306,
    'charset': 'utf8'
}

db = MySQLDatabase("stock", **settings)
