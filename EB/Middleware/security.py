import jwt
from Context.Context import Context
# from EB.Context.Context import Context
from time import time
import os
from functools import wraps
from flask import request, Response
_context = Context.get_default_context()


def hash_password(pwd):
    global _context
    h = jwt.encode(pwd, key=_context.get_context("JWT_SECRET"))
    h = str(h.decode('utf-8'))
    return h

def decode_token(token):
    decoded = jwt.decode(token, key=os.environ['jwt_secret'], algorithm='HS256')
    return decoded

def generate_token(info):

    info["timestamp"] = time()
    email = info['email']

    adminEmails = os.environ['admin_emails']
    if email in adminEmails:
        info['role']='admin'
    else:
        info['role']='student'

    # info['created'] = str(info['created'])

    h = jwt.encode(info, key=_context.get_context("JWT_SECRET"))
    h = str(h.decode('utf-8'))

    return h


def authorize(f):
    def decorated_function(*args, **kwargs):
        if request.method == 'PUT' or request.method == 'DELETE':
            authToken = request.headers.get('Authorization')
            if authToken:
                decoded = decode_token(authToken)
                print(decoded)
                if (time() - decoded['timestamp']) > float(os.environ['timeout']):
                    rsp_txt = 'User login session timed out. Please log in again.'
                else:
                    if request.method == 'DELETE' and decoded['role'] != 'admin':
                        rsp_txt = 'Administrator rights are required to perform this action'
                    elif request.method == 'PUT' and decoded['email'] != request.view_args['email']:
                        rsp_txt = 'You may not update data for other users.'
                    else:
                        return f(*args, **kwargs)
            else:
                rsp_txt = 'Please log in to perform this action'
            rsp = Response(rsp_txt, status=200, content_type="application/json")
            return rsp
        else:
            return f(*args, **kwargs)
    return decorated_function



