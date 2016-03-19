from flask.ext.wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired


class CityForm(Form):
    state = StringField('state', validators=[DataRequired()])
    city = StringField('city', validators=[DataRequired()])
