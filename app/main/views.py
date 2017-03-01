from flask import render_template,session,redirect,url_for,abort,flash
from flask_login import login_required,current_user
from . import main
from .forms import QuestionForm,AnswerForm,EditProfileForm,EditProfileAdminForm
from .. import db
from ..models import User,Role,Topic,Question,Answer,Comment
from ..decorators import admin_required
from ..activity.forms import CommentForm

@main.route('/',methods=['GET','POST'])
def index():
    return render_template('index.html')

@main.route('/user/<username>')
def user(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('user.html',user=user)

@main.route('/question/<int:id>',methods=['GET','POST'])
@login_required
def question(id):
    question=Question.query.get(id)
    if question is None:
        abort(404)
    form = AnswerForm()
    if form.validate_on_submit():
        answer=Answer(content=form.content.data,
                      question=question,
                      author=current_user._get_current_object())
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('.question',id=question.id))
    return render_template('question.html',question=question,form=form)

@main.route('/ask',methods=['GET','POST'])
@login_required
def ask():
    form=QuestionForm()
    if form.validate_on_submit():
        question=Question(description=form.description.data,
                          title=form.title.data,
                          asker=current_user._get_current_object())
        question.add_topics(form.topic.data)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('.question',id=question.id))
    return render_template('ask.html',form=form)

@main.route('/answer/<int:id>',methods=['GET','POST'])
@login_required
def answer(id):
    answer=Answer.query.get(id)
    if answer is None:
        abort(404)
    form =CommentForm()
    if form.validate_on_submit():
        comment=Comment(content=form.content.data,
                        answer=answer,
                        author=current_user._get_current_object())
        db.session.add(comment)
        return redirect(url_for('.answer',id=answer.id))
    return render_template('answer.html',answer=answer,form=form)

@main.route('/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form=EditProfileForm()
    if form.validate_on_submit():
        current_user.location=form.location.data
        current_user.about_me=form.about_me.data
        db.session.add(current_user)
        flash('你的个人信息已更新')
        return redirect(url_for('.user',username=current_user.username))
    form.location.data=current_user.location
    form.about_me.data=current_user.about_me
    return render_template('edit_profile.html',form=form)

@main.route('/edit-profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user=User.query.get_or_404(id)
    form=EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email=form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)#注意，添加外键的用法
        user.location = form.location.data
        user.about_me = form.about_me.data
        flash('个人信息已更新')
        return redirect(url_for('.user', username=user.username))
    form.username.date = user.username
    form.email.data=user.email
    form.confirmed.data=user.confirmed
    form.role.data=user.role_id#注意
    form.location.data=user.location
    form.about_me.data=user.about_me
    return render_template('edit_profile.html',form=form,user=user)