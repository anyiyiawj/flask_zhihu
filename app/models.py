from werkzeug.security import generate_password_hash,check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
from flask import current_app
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from . import db

class Permission:
    USER=0x01
    ASK=0x02
    WRITE_ANSWER=0x04
    MODERATE=0x08
    ADMINISTER=0x80

class Role(db.Model):
    __tablename__='roles'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True)
    permissions = db.Column(db.Integer)
    default = db.Column(db.Boolean, default=True, index=True)
    users=db.relationship('User',backref='role',lazy='dynamic')

    @staticmethod
    def insert_role():
        roles={
            'User':(Permission.USER|
                    Permission.ASK|
                    Permission.WRITE_ANSWER,True),
            'Moderator':(Permission.USER|
                            Permission.ASK|
                            Permission.WRITE_ANSWER|
                            Permission.MODERATE,False),
            'Administrator': (0xff,False )
        }
        for r in roles:
            role=Role.query.filter_by(name=r).first()
            if role is None:
                role=Role(name=r)
            role.permissions=roles[r][0]
            role.default=roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>'%self.name

class User(UserMixin,db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(64),unique=True,index=True)
    username=db.Column(db.String(64),unique=True,index=True)
    location=db.Column(db.String(64))
    about_me=db.Column(db.Text())#自我介绍
    member_since=db.Column(db.DateTime(),default=datetime.utcnow)#注册信息
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow)
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))
    password_hash=db.Column(db.String(128))
    confirmed=db.Column(db.Boolean,default=False)

    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email==current_app.config['ZHIHU_ADMIN']:
                self.role=Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role=Role.query.filter_by(default=True).first()

    def can(self,permissions):
        return self.role is not None and (self.role.permissions & permissions)==permissions

    def is_administrator(self):
        return  self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen=datetime.utcnow()
        db.session.add(self)
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    def generate_confirmation_token(self,expiration=3600):
        s=Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        return s.dumps({'confirm':self.id})

    def confirm(self,token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        if data.get('confirm')!=self.id:
            return False
        self.confirmed=True
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>'%self.username

class AnonymousUser(AnonymousUserMixin):#未注册的人
    def can(self,permission):
        return False

    def is_administrator(self):
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
