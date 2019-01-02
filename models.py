from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *


DATABASE = SqliteDatabase('worklog.db')


class BaseModel(Model):
    class Meta:
        database = DATABASE
        order_by = ('-id', )


class User(UserMixin, BaseModel):
    username = CharField()
    password = CharField()

    @classmethod
    def create_user(cls, username, password):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    password=generate_password_hash(password))
        except IntegrityError:
            raise ValueError("User already exists")


class Entry(BaseModel):
    title = CharField()
    date = DateField()
    duration = CharField()
    learned = TextField()
    resources = TextField()
    slug = CharField(unique=True)

    def get_tags(self):
        """ Return tags related to post """
        return Tag.select().where(Tag.entry == self)


class Tag(BaseModel):
    tag = CharField()
    entry = (ForeignKeyField(Entry, related_name='tags'))
    slug = CharField()


def initialize():
    """ Initialize and create the database/tables """
    DATABASE.connect()
    DATABASE.create_tables([User, Entry, Tag], safe=True)
    DATABASE.close()
