from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from m_app import db
from m_app.models import User, Task


def users(count=100):
    # fake = Faker()
    i = 0
    while i < count:
        u = User(email='user_'+str(i)+'@admin.com',
                 username='user_'+str(i),
                 password='password',
                 confirmed=True,
                 name='user'+str(i),
                 location='Kiev',
                 about_me='user_'+str(i))
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def tasks(count=100):
    # fake = Faker()
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Task(title='task_'+str(i),
                 body='task_body_'+str(i),
                 author=u)
        db.session.add(p)
    db.session.commit()

if __name__ == '__main__':
    users(20)
    tasks(50)
