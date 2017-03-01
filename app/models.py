from werkzeug.security import generate_password_hash,check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
import hashlib
from flask import current_app,request
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

class Follow(db.Model):
    __tablename__='follows'
    follower_id=db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)#关注者，外键
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)#被关注者，外键
    timestamp=db.Column(db.DateTime,default=datetime.utcnow)

class User(UserMixin,db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(64),unique=True,index=True)
    avatar_hash=db.Column(db.String(32))
    username=db.Column(db.String(64),unique=True,index=True)
    location=db.Column(db.String(64))
    about_me=db.Column(db.Text())#自我介绍
    member_since=db.Column(db.DateTime(),default=datetime.utcnow)#注册信息
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow)
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))
    password_hash=db.Column(db.String(128))
    confirmed=db.Column(db.Boolean,default=False)
    questions = db.relationship('Question', backref='asker', lazy='dynamic')
    answers = db.relationship('Answer', backref='author', lazy='dynamic')
    comments=db.relationship('Comment',backref='author',lazy='dynamic')
    followed=db.relationship('Follow',foreign_keys=[Follow.follower_id],
                             backref=db.backref('follower',lazy='joined'),
                             lazy='dynamic',cascade='all,delete-orphan')#我关注的人
    followers=db.relationship('Follow',foreign_keys=[Follow.followed_id],
                             backref=db.backref('followed',lazy='joined'),
                             lazy='dynamic',cascade='all,delete-orphan')#谁关注我

    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email==current_app.config['ZHIHU_ADMIN']:
                self.role=Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role=Role.query.filter_by(default=True).first()
        if self.email  is not None and self.avatar_hash is None:
            self.avatar_hash=hashlib.md5(self.email.encode('utf-8')).hexdigest()

    def can(self,permissions):
        return self.role is not None and (self.role.permissions & permissions)==permissions

    def is_administrator(self):
        return  self.can(Permission.ADMINISTER)

    def gravatar(self,size=100,default='identicon',rating='g'):
        if request.is_secure:
            url='https://secrue.gravatar.com/avatar'
        else:
            url='http://www.gravatar.com/avatar'
        hash=self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url,hash=hash,size=size,default=default,rating=rating)

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

    def follow(self,user):
        if not self.is_following(user):
            f=Follow(follower_id=self.id, followed_id=user.id)#可以直接调用，也可以用id
            db.session.add(f)

    def unfollow(self,user):
        f=self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self,user):#是否关注这个人
        return self.followed.filter_by(followed_id=user.id).first() is not None
    #查询的时候filter_by用id来查
    def is_followed_by(self,user):#是否被这个人关注
        return self.follwers.filter_by(follower_id=user.id).first() is not None

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

descs=db.Table('descs',
    db.Column('topic_id',db.Integer,db.ForeignKey('topics.id')),
    db.Column('question_id',db.Integer,db.ForeignKey('questions.id'))
)#topic和question之间的多对多关系

class Topic(db.Model):
    __tablename__='topics'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True)
    questions = db.relationship('Question', secondary=descs,
                                backref=db.backref('topics',lazy='dynamic'),lazy='dynamic')

class Question(db.Model):
    __tablename__='questions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64),unique=True)
    description=db.Column(db.Text())
    create_time = db.Column(db.DateTime(), default=datetime.utcnow)
    asker_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    answers=db.relationship('Answer',backref='question',lazy='dynamic')

    def add_topics(self,string):
        list = string.split()
        for i in list:
            if Topic.query.filter_by(name=i).first():
                self.topics.append(Topic.query.filter_by(name=i).first())
            else:
                topic=Topic(name=i)
                db.session.add(topic)
                self.topics.append(topic)

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text())
    answer_time=db.Column(db.DateTime(),default=datetime.utcnow)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments=db.relationship('Comment',backref='answer',lazy='dynamic')
    def __repr__(self):
        return '<Comm %r>'%self.content

class Comment(db.Model):
    __tablename__='comments'
    id=db.Column(db.Integer,primary_key=True)
    content=db.Column(db.Text())
    create_time=db.Column(db.DateTime(),default=datetime.utcnow)
    answer_id=db.Column(db.Integer,db.ForeignKey('answers.id'))
    commenter_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    def __repr__(self):
        return '<Comm %r>'%self.content