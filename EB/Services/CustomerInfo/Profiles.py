from Context.Context import Context
from DataAccess.DataObject import ProfilesRDB as ProfilesRDB
import uuid
import boto3
import os
import requests


# The base classes would not be IN the project. They would be in a separate included package.
# They would also do some things.

class ServiceException(Exception):
    unknown_error = 9001
    missing_field = 9002
    bad_data = 9003

    def __init__(self, code=unknown_error, msg="Oh Dear!"):
        self.code = code
        self.msg = msg


class BaseService():
    missing_field = 2001

    def __init__(self):
        pass


class ProfilesService(BaseService):
    required_create_fields = ['customer_id', 'type', 'subtype', 'value']
    valid_types = ['Email', 'Address', 'Telephone', 'Other']
    valid_subtypes = ['Work', 'Home', 'Mobile', 'Other']

    def __init__(self, ctx=None):

        if ctx is None:
            ctx = Context.get_default_context()

        self._ctx = ctx

    @classmethod
    def get_first(cls):
        return ProfilesRDB.get_first()

    @classmethod
    def get_queried(cls, queries):
        return ProfilesRDB.get_queried(queries)

    @classmethod
    def create_profile_entry(cls, profile_entry_info):
        for f in ProfilesService.required_create_fields:
            v = profile_entry_info.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)
        profile_entry_info = { k: profile_entry_info[k] for k in ProfilesService.required_create_fields }

        if profile_entry_info['type'] not in ProfilesService.valid_types:
            raise ServiceException('Invalid type was supplied!')
        if profile_entry_info['subtype'] not in ProfilesService.valid_subtypes:
            raise ServiceException('Invalid subtype was supplied!')

        if profile_entry_info['type'] == 'Address':
            address_microservice_body = {"address":profile_entry_info['value']}
            req = requests.post(os.environ['address_microservice_url'], json=address_microservice_body)
            if req.status_code == 200:
                profile_entry_info['value'] = "/address/" + req.text
            else:
                print(req.text)
                raise ServiceException('An invalid address was supplied to create a profile entry!')


        profile_entry_info['profile_entry_id'] = str(uuid.uuid4())
        result = ProfilesRDB.create_profile_entry(profile_entry_info)
        return result

    @classmethod
    def get_by_customer_id(cls, customer_id):
        result = ProfilesRDB.get_by_customer_id(customer_id)
        return result

    @classmethod
    def get_by_profile_entry_id(cls, profile_entry_id):
        result = ProfilesRDB.get_by_profile_entry_id(profile_entry_id)
        return result

    @classmethod
    def delete_profile_entry(cls, profile_entry_id):
        result = ProfilesRDB.delete_profile_entry(profile_entry_id)
        return result

    @classmethod
    def update_profile_entry(cls, body, profile_entry_id, existing):
        for k in body.keys():
            if k not in ProfilesService.required_create_fields:
                raise ServiceException("Attempting to update unsupported field!")
            if k == 'type' and body['type'] not in ProfilesService.valid_types:
                raise ServiceException('Invalid type was supplied!')
            if k == 'subtype' and body['subtype'] not in ProfilesService.valid_subtypes:
                raise ServiceException('Invalid subtype was supplied!')
        if existing['type'] == 'Address' and 'value' in body.keys():
            address_microservice_body = {"address": body['value']}
            req = requests.post(os.environ['address_microservice_url'], json=address_microservice_body)
            if req.status_code == 200:
                body['value'] = "/address/" + req.text
            else:
                raise ServiceException('An invalid address was supplied to update the profile entry!')
        result = ProfilesRDB.update_profile_entry(profile_entry_id, body)
        return result

    #
    # @classmethod
    # def create_user(cls, user_info):
    #     for f in UsersService.required_create_fields:
    #         v = user_info.get(f, None)
    #         if v is None:
    #             raise ServiceException(ServiceException.missing_field,
    #                                    "Missing field = " + f)
    #
    #         if f == 'email':
    #             if v.find('@') == -1:
    #                 raise ServiceException(ServiceException.bad_data,
    #                                        "Email looks invalid: " + v)
    #
    #     user_info['id'] = str(uuid.uuid4())
    #     user_info["status"] = "PENDING"
    #     result = UsersRDB.create_user(user_info=user_info)
    #     print(os.environ['region_name'])
    #     print(os.environ['aws_access_key_id'])
    #     print(os.environ['aws_secret_access_key'])
    #     client = boto3.client('sns',
    #                           region_name=os.environ['region_name'],
    #                           aws_access_key_id=os.environ['aws_access_key_id'],
    #                           aws_secret_access_key=os.environ['aws_secret_access_key'])
    #
    #     response = client.publish(
    #         TopicArn='arn:aws:sns:ca-central-1:969112874411:E6156CustomerChange',
    #         Subject='New Registration',
    #         Message='{"customers_email":"%s"}' % user_info['email'],
    #     )
    #
    #     return result
    #
    # @classmethod
    # def update_user(cls, user_info, email):
    #     result = UsersRDB.update_user(email, user_info=user_info)
    #     return result
    #
    # @classmethod
    # def delete_user(cls, email):
    #
    #     result = UsersRDB.delete_user(email)
    #     return result
    #
    #
