import asyncio
import os
import sys

from dotenv import dotenv_values, load_dotenv
from pyaml_env import parse_config
from sanic import Sanic
from sqlalchemy.future import select
from werkzeug.security import generate_password_hash

from app.api import auth_api, private_user_api, user_api
from app.db import Db
from app.di import DI
from app.model.tables import User


def get_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        config_path = os.path.abspath(os.path.join(__file__, '../.'))
        return config_path


if __name__ == "__main__":
    load_dotenv()

    config_dict = parse_config(os.path.join(get_root(), 'config.yml'))

    config = {
        **config_dict,
        **dict(dotenv_values()),
        **dict(os.environ),
    }

    app = Sanic("Kefir_cv_test")
    app.config.API_VERSION = '0.1.0'
    app.config.API_TITLE = 'Kefir Python Junior Test'

    di = DI(
        app=app,
        config=config,
    )

    di.add(db=Db(di))

    app.blueprint(auth_api(di))
    app.blueprint(user_api(di))
    app.blueprint(private_user_api(di))
    app.config['OAS_UI_DEFAULT'] = 'swagger'
    app.config['OAS_URL_PREFIX'] = '/swagger'

    if os.name == 'posix':
        import uvloop
        asyncio.set_event_loop(uvloop.new_event_loop())
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    first_admin_dict = di.config['db_admin']
    first_admin = User(
        first_name=first_admin_dict['first_name'],
        last_name=first_admin_dict['last_name'],
        email=first_admin_dict['email'],
        is_admin=first_admin_dict['is_admin'],
        password_hash=generate_password_hash(first_admin_dict['password'])
    )
    sql = select(User.__table__.c.is_admin).where(User.email == first_admin.email)
    asyncio.run(di.db.db_start(sql, first_admin))

    app.run(
        host=di.config['web']['host'],
        port=di.config['web']['port'],
        debug=False,
    )
