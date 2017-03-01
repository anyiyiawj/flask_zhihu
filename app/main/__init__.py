from flask import Blueprint
from app.models import Permission,User,Answer,Comment
main=Blueprint('main',__name__)

from . import views,errors

@main.app_context_processor#上下文处理器，每次调用render_template多个模板参数
def inject_permission():
    return dict(Permission=Permission,User=User,Answer=Answer,Comment=Comment)