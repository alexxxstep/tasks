from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length
from flask_pagedown.fields import PageDownField
from wtforms_sqlalchemy.fields import QuerySelectField
from ..models import Status


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class TaskForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    body = TextAreaField("Body", validators=[DataRequired()])
    # status = SelectField('New status', coerce=int)
    submit = SubmitField('Submit')


class TaskCommentForm(FlaskForm):
    status = SelectField('New status', coerce=int)
    body = TextAreaField("Comment")
    submit = SubmitField('Save')


class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')
