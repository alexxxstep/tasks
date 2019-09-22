from datetime import datetime
from flask import render_template, session, redirect, url_for, \
    abort, flash, request, current_app
from flask_login import login_required, current_user
from . import main
from .forms import NameForm, TaskForm, EditProfileForm, TaskCommentForm
from .. import db
from ..models import User, Role, Task, Comment, Status


# from ..decorators import admin_required

@main.route('/', methods=['GET', 'POST'])
def index():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(title=form.title.data, body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    pagination = Task.query.order_by(Task.date_created.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    tasks = pagination.items
    return render_template('index.html', form=form, tasks=tasks,
                           pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    tasks = user.tasks.order_by(Task.date_created.desc()).all()
    return render_template('user.html', user=user, tasks=tasks)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/task/<int:id>', methods=['GET', 'POST'])
def task(id):
    task = Task.query.get_or_404(id)
    comments = Comment.query.filter_by(task=task).all()
    n_comments = Comment.query.filter_by(task=task).count()
    form = TaskCommentForm()

    form.status.choices = [(row.id, row.name) for row in Status.query.all()]

    if form.validate_on_submit():
        new_status_id = form.status.data

        if new_status_id != task.status_id and new_status_id > 1:
            task.status_id = new_status_id

            close_sts = Status.query.filter_by(name='closed').first()
            cancell_sts = Status.query.filter_by(name='cancelled').first()
            if close_sts is not None:
                if new_status_id == close_sts.id:
                    task.done = True
            if cancell_sts is not None:
                if new_status_id == cancell_sts.id:
                    task.done = True

            db.session.add(task)
            db.session.commit()
            flash('Update new status')


        if form.body.data:
            comment = Comment(task=task,
                              commentator=current_user._get_current_object(),
                              body=form.body.data)
            db.session.add(comment)
            db.session.commit()
            flash('The task has been commented.')


        return redirect(url_for('.task', id=task.id))

    return render_template('task.html', task=task, form=form, comments=comments, n_comments=n_comments)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    task = Task.query.get_or_404(id)

    if current_user != task.author:
        abort(403)
    form = TaskForm()
    if form.validate_on_submit():
        task.title = form.title.data
        task.body = form.body.data
        db.session.add(task)
        db.session.commit()

        flash('The task has been updated.')
        return redirect(url_for('.task', id=task.id))
    form.title.data = task.title
    form.body.data = task.body
    return render_template('edit_task.html', form=form)
