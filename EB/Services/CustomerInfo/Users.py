from abc import ABC, abstractmethod
from Context.Context import Context
from DataAccess.DataObject import UsersRDB as UsersRDB
import uuid
import boto3
import os

# The base classes would not be IN the project. They would be in a separate included package.
# They would also do some things.

class ServiceException(Exception):

    unknown_error   =   9001
    missing_field   =   9002
    bad_data        =   9003

    def __init__(self, code=unknown_error, msg="Oh Dear!"):
        self.code = code
        self.msg = msg


class BaseService():

    missing_field   =   2001

    def __init__(self):
        pass


class UsersService(BaseService):

    required_create_fields = ['last_name', 'first_name', 'email', 'password']

    def __init__(self, ctx=None):

        if ctx is None:
            ctx = Context.get_default_context()

        self._ctx = ctx

    @classmethod
    def get_first(cls):
        return UsersRDB.get_first()

    @classmethod
    def get_by_email(cls, email):

        result = UsersRDB.get_by_email(email)
        return result

    @classmethod
    def create_user(cls, user_info):
        for f in UsersService.required_create_fields:
            v = user_info.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)

            if f == 'email':
                if v.find('@') == -1:
                    raise ServiceException(ServiceException.bad_data,
                           "Email looks invalid: " + v)

        user_info['id'] = str(uuid.uuid4())
        user_info["status"] = "PENDING"
        result = UsersRDB.create_user(user_info=user_info)
        print(os.environ['region_name'])
        print(os.environ['aws_access_key_id'])
        print(os.environ['aws_secret_access_key'])
        client = boto3.client('sns',
                              region_name = os.environ['region_name'],
                              aws_access_key_id = os.environ['aws_access_key_id'],
                              aws_secret_access_key = os.environ['aws_secret_access_key'])
        
        response = client.publish(
            TopicArn='arn:aws:sns:ca-central-1:969112874411:E6156CustomerChange',
            Subject='New Registration',
            Message='{"customers_email":"%s"}'%user_info['email'],
        )

        return result

    @classmethod
    def update_user(cls, user_info, email):
        result = UsersRDB.update_user(email, user_info=user_info)
        return result

    @classmethod
    def delete_user(cls, email):

        result = UsersRDB.delete_user(email)
        return result


