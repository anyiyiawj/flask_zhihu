from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField,BooleanField,SelectField
from wtforms.validators import Length,Required,Email,Regexp
from wtforms import ValidationError
from ..models import Role,User

class QuestionForm(FlaskForm):
    title=StringField('问题',validators=[Required()])
    description=TextAreaField('问题描述')
    topic=StringField('添加话题')
    submit = SubmitField('提交')

class AnswerForm(FlaskForm):
    context=TextAreaField('回答')
    submit = SubmitField('提交')

class EditProfileForm(FlaskForm):
    location=StringField('地址',validators=[Length(0,64)])
    about_me=TextAreaField('我的简介')
    submit=SubmitField('提交')

class EditProfileAdminForm(FlaskForm):
    email=StringField('邮箱',validators=[Required(),Length(1, 64), Email()])
    username = StringField('用户名', validators=[Required(), Length(1, 64),
                            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, '用户名由字母，数字下划线和点组成')])
    confirmed=BooleanField('认证状态')
    role=SelectField('权限',coerce=int)#下拉列表的实现，取整数值
    location=StringField('地址',validators=[Length(0,64),])
    about_me=TextAreaField('介绍')
    submit=SubmitField('提交')

    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        self.role.choices=[(role.id,role.name)
                           for role in Role.query.order_by(Role.name).all()]#选项，元组的列表
        self.user=user

    def validate_email(self,field):
        if field.data!=self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已经被注册.')

    def validate_username(self,field):
        if field.data!=self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被占用')