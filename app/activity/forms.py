from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import Required

class CommentForm(FlaskForm):
    content=StringField('评论',validators=[Required()])
    submit = SubmitField('提交')