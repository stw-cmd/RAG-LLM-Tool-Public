# app/auth/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class RegistrationForm(FlaskForm):
    # Username field required and 3-100 characters long
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=100)]
    )
    # Email field required and must be a valid email format
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    # Password field required and at least 6 characters long
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)]
    )
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    # Username field required for login
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=100)]
    )
    # Password field required for login
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    submit = SubmitField('Login')