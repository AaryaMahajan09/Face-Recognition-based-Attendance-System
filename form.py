from wtforms import StringField, EmailField, SubmitField, PasswordField
from flask_wtf import FlaskForm
from wtforms.validators import Length, DataRequired, Email

class RegistrationForms(FlaskForm):

    name = StringField("Name:",validators=[DataRequired()])
    email = EmailField("Email-ID:", validators=[DataRequired(), Email()])
    password = PasswordField("Password:", validators=[DataRequired(), Length(min=6)])

    submit = SubmitField("Register")