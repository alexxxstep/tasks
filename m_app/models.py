import hashlib
import enum
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager
from datetime import datetime
from markdown import markdown
import bleach


# class StatusTask:
#     status = {
#     'development': DevelopmentConfig,
#     'testing': TestingConfig,
#     'production': ProductionConfig,
#
#     'default': DevelopmentConfig
# }
class Status(db.Model):
    __tables__ = 'status'
    STATUS_LIST = ['new', 'in work', 'executed', 'closed', 'cancelled']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    tasks = db.relationship('Task', backref='status', lazy='dynamic')

    def __repr__(self):
        return self.name


class Task(db.Model):
    __tables__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True)
    body = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    done = db.Column(db.Boolean, default=False, index=True)
    title_html = db.Column(db.Text)
    comments = db.relationship('Comment', backref='task', lazy='dynamic')
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'))


    def __init__(self, **kwargs):
        super(Task, self).__init__(**kwargs)
        if self.status_id is None:
            self.status = Status.query.filter_by(name='new').first()

    @staticmethod
    def on_changed_title(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']

        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))



    # def change_status(self, token):
    #
    #     s = Serializer(current_app.config['SECRET_KEY'])
    #     try:
    #         data = s.loads(token.encode('utf-8'))
    #     except:
    #         return False
    #     if data.get('change_status') != self.id:
    #         return False
    #     new_status = data.get('new_status')
    #     if new_status is None:
    #         return False


        # s_closed = TaskStatus.query.filter_by(name='closed').first()
        # if new_status == s_closed:
        #     self.done = True
        #
        # self.status = new_status
        #
        #
        # db.session.add(self)
        # return True





db.event.listen(Task.title, 'set', Task.on_changed_title)


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer, default=16)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    # @staticmethod
    # def insert_roles():
    #     roles = {
    #         'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
    #         'Moderator': [Permission.FOLLOW, Permission.COMMENT,
    #                       Permission.WRITE, Permission.MODERATE],
    #         'Administrator': [Permission.FOLLOW, Permission.COMMENT,
    #                           Permission.WRITE, Permission.MODERATE,
    #                           Permission.ADMIN],
    #     }
    #     default_role = 'User'
    #     for r in roles:
    #         role = Role.query.filter_by(name=r).first()
    #         if role is None:
    #             role = Role(name=r)
    #         role.reset_permissions()
    #         for perm in roles[r]:
    #             role.add_permission(perm)
    #         role.default = (role.name == default_role)
    #         db.session.add(role)
    #     db.session.commit()
    #
    # def add_permission(self, perm):
    #     if not self.has_permission(perm):
    #         self.permissions += perm
    #
    # def remove_permission(self, perm):
    #     if self.has_permission(perm):
    #         self.permissions -= perm
    #
    # def reset_permissions(self):
    #     self.permissions = 0
    #
    # def has_permission(self, perm):
    #     return self.permissions & perm == perm

    def __repr__(self):
        return f'Role {self.name}'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    commentator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    tasks = db.relationship('Task', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='commentator', lazy='dynamic')


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
            if self.email is not None and self.avatar_hash is None:
                self.avatar_hash = self.gravatar_hash()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, _password):
        self.password_hash = generate_password_hash(_password)

    def verify_password(self, _password):
        return check_password_hash(self.password_hash, _password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    # def can(self, perm):
    #     return self.role is not None and self.role.has_permission(perm)
    #
    # def is_administrator(self):
    #     return self.can(Permission.ADMIN)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def __repr__(self):
        return f'User {self.username}'


class AnonymousUser(AnonymousUserMixin):
    # def can(self, permission):
    #     return False
    #
    # def is_administrator(self):
    #     return False
    pass


# login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
