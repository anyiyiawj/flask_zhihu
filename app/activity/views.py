from flask import flash,redirect,url_for,request,render_template,current_app
from flask_login import login_required,current_user
from app.decorators import permission_required
from app.models import Permission,User
from . import activity

@activity.route('/follow/<username>')
@login_required
@permission_required(Permission.USER)
def follow(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('语法错误')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash("你已经关注这个用户了")
        return redirect(url_for('main.user',username=username))
    current_user.follow(user)
    flash('你已经关注了%s。'%username)
    return redirect(url_for('main.user',username=username))

@activity.route('/unfollow/<username>')
@login_required
@permission_required(Permission.USER)
def unfollow(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('语法错误')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash("你没有关注这个用户了")
        return redirect(url_for('main.user',username=username))
    current_user.unfollow(user)
    flash('你已经取消关注%s。'%username)
    return  redirect(url_for('main.user',username=username))

@activity.route('/followers/<username>')
def followers(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('语法错误')
        return redirect(url_for('main.index'))
    page=request.args.get('page',1,type=int)
    pagination=user.followers.paginate(page,
            per_page=current_app.config['ZHIHU_FOLLOWERS_PER_PAGE'],error_out=False)
    follows=[{'user':item.follower,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html',user=user,endpoint='.followers',title="的追随者",
                           pagination=pagination,follows=follows)

@activity.route('/followereds/<username>')
def followered_by(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('语法错误')
        return redirect(url_for('main.index'))
    page=request.args.get('page',1,type=int)
    pagination=user.followed.paginate(page,
            per_page=current_app.config['ZHIHU_FOLLOWERS_PER_PAGE'],error_out=False)
    follows=[{'user':item.follower,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html',user=user,endpoint='.followers',title="所关注的人",
                           pagination=pagination,follows=follows)
