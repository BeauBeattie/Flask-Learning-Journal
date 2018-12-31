from flask_wtf import Form
from wtforms import StringField, PasswordField, TextAreaField, DateField
from wtforms.validators import (DataRequired, Regexp, ValidationError,
                                Length)

from models import User


class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class EntryForm(Form):
    title = StringField("Title", validators=[DataRequired()])
    date = DateField('Date: DD-MM-YYYY',
                     validators=[DataRequired()], format='%d-%m-%Y')
    duration = StringField("Time Spent", validators=[DataRequired()])
    learned = TextAreaField("Learned", validators=[DataRequired()])
    resources = TextAreaField("Resources used", validators=[DataRequired()])


class TagForm(Form):
    tags = StringField("Tags - seperate by commas (optional)", default="")
