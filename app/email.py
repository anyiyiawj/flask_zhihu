from threading import Thread
from flask import render_template
from flask_mail import Message
from ..app import mail
from  ..manage import app

def send_async_email(app,msg):
    with app.app_context():#上下文
        mail.send(msg)

def send_email(to,subject,template,**kwargs):
    msg=Message(app.config['ZHIHU_MAIL_PREFIX']+subject,
                sender=app.config['ZHIHU_MAIL_SENDER'],recipients=[to])
    msg.body=render_template(template+'.txt',**kwargs)
    msg.html=render_template(template+'html',**kwargs)
    thr=Thread(target=send_async_email,args=[app,msg])
    thr.start()
    return thr
