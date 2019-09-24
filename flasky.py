import os
from m_app import create_app
from m_app import db
from m_app.models import *
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy

app = create_app('default')

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)



@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    app.run(debug=True, port=4999)

