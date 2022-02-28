from datetime import datetime, timedelta

import jwt
from sanic.exceptions import Unauthorized


def create_token(di, email):
    payload = {
        'exp': datetime.utcnow() + timedelta(seconds=di.config['web']['jwt_lifespan']),
        'email': str(email)
    }
    token = jwt.encode(
        payload,
        di.config['web']['jwt_secret'],
        algorithm=di.config['web']['jwt_algorithm'],
    )
    return token


def verify_token(di, token):
    try:
        payload = jwt.decode(
            token,
            di.config['web']['jwt_secret'],
            algorithms=[di.config['web']['jwt_algorithm']],
        )
    except:
        raise Unauthorized("Response 401 Current User Users Current Get")
    return payload.get('email')








