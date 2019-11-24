# Import functions and objects the microservice needs.
# - Flask is the top-level application. You implement the application by adding methods to it.
# - Response enables creating well-formed HTTP/REST responses.
# - requests enables accessing the elements of an incoming HTTP/REST request.
#
from flask import Flask, Response, request

from datetime import datetime
import json
import werkzeug.http
import copy
from Services.CustomerInfo.Users import UsersService as UserService
from Services.CustomerInfo.Profiles import ProfilesService as ProfileService
from Context.Context import Context
from Services.RegisterLogin.RegisterLogin import RegisterLoginSvc as RegisterLoginSvc
# import EB.Middleware.security as security
# from EB.Middleware.security import authorize
from Middleware.security import authorize
import time
import os
# from Services.BaseballData import BaseballData as BaseballData

# Setup and use the simple, common Python logging framework. Send log messages to the console.
# The application should get the log level out of the context. We will change later.
#
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
###################################################################################################################
#
# AWS put most of this in the default application template.
#
# AWS puts this function in the default started application
# print a nice greeting.
def say_hello(username="World"):
    return '<p>Hello %s!</p>\n' % username

# AWS put this here.
# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>EB Flask Test</title> </head>\n<body>'''
instructions = '''
    <p><em>Hint</em>: This is a RESTful web service! Append a username
    to the URL (for example: <code>/Thelonious</code>) to say hello to
    someone specific.</p>\n'''
home_link = '<p><a href="/">Back</a></p>\n'
footer_text = '</body>\n</html>'

# EB looks for an 'application' callable by default.
# This is the top-level application that receives and routes requests.
application = Flask(__name__)

# add a rule for the index page. (Put here by AWS in the sample)
application.add_url_rule('/', 'index', (lambda: header_text +
    say_hello() + instructions + footer_text))

# add a rule when the page is accessed with a name appended to the site
# URL. Put here by AWS in the sample
application.add_url_rule('/<username>', 'hello', (lambda username:
    header_text + say_hello(username) + home_link + footer_text))

##################################################################################################################
# The stuff I added begins here.

_default_context = None
_user_service = None
_profile_service = None
_registration_service = None

def _get_default_context():
    global _default_context

    if _default_context is None:
        _default_context = Context.get_default_context()

    return _default_context


def _get_user_service():
    global _user_service

    if _user_service is None:
        _user_service = UserService(_get_default_context())

    return _user_service

def _get_profile_service():
    global _profile_service

    if _profile_service is None:
        _profile_service = ProfileService(_get_default_context())

    return _profile_service

def _get_registration_service():
    global _registration_service

    if _registration_service is None:
        _registration_service = RegisterLoginSvc()

    return _registration_service

def init():
    global _default_context, _user_service, _profile_service

    _default_context = Context.get_default_context()
    _user_service = UserService(_default_context)
    _profile_service = ProfileService(_default_context)


    logger.debug("_user_service = " + str(_user_service))


# 1. Extract the input information from the requests object.
# 2. Log the information
# 3. Return extracted information.
#

def log_and_extract_input(method, path_params=None):
    path = request.path
    args = dict(request.args)
    data = None
    headers = dict(request.headers)
    method = request.method

    try:
        if request.data is not None:
            data = request.json
        else:
            data = None
    except Exception as e:
        # This would fail the request in a more real solution.
        data = "You sent something but I could not get JSON out of it."

    log_message = str(datetime.now()) + ": Method " + method

    inputs = {
        "path": path,
        "method": method,
        "path_params": path_params,
        "query_params": args,
        "headers": headers,
        "body": data
    }

    log_message += " received: \n" + json.dumps(inputs, indent=2)
    logger.debug(log_message)

    return inputs

def log_response(method, status, data, txt):
    msg = {
        "method": method,
        "status": status,
        "txt": txt,
        "data": data
    }

    logger.debug(str(datetime.now()) + ": \n" + json.dumps(msg, indent=2))


# This function performs a basic health check. We will flesh this out.
@application.route("/health", methods=["GET"])
def health_check():
    rsp_data = { "status": "healthy", "time": str(datetime.now()) }
    rsp_str = json.dumps(rsp_data)
    rsp = Response(rsp_str, status=200, content_type="application/json")
    return rsp


@application.route("/demo/<parameter>", methods=["GET", "POST"])
def demo(parameter):
    inputs = log_and_extract_input(demo, { "parameter": parameter })

    msg = {
        "/demo received the following inputs" : inputs
    }

    rsp = Response(json.dumps(msg), status=200, content_type="application/json")
    return rsp


@application.route("/api/registration", methods=["POST"])
def register_user():
    inputs = log_and_extract_input(demo, {"parameters": None})
    rsp_data = None
    rsp_status = None
    rsp_txt = None

    try:

        r_svc = _get_registration_service()

        logger.error("/api/registration: _r_svc = " + str(r_svc))

        if inputs["method"] == "POST":

            rsp, tok = r_svc.register(inputs['body'])

            if rsp is not None:
                rsp_data = rsp
                rsp_status = 201
                rsp_txt = "CREATED"
                link = rsp_data[0]
                auth = rsp_data[1]
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NOT FOUND"
        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:

            headers = {"Location": "/api/users/" + link}
            headers["Authorization"] = auth
            full_rsp = Response(rsp_txt, headers=headers,
                                status=rsp_status, content_type="text/plain")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        log_msg = "/api/registration: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/api/registration", rsp_status, rsp_data, rsp_txt)

    return full_rsp


@application.route("/api/user/", methods=["GET", "POST"])
def user():
    global _user_service
    inputs = log_and_extract_input(demo)
    rsp_data = None

    try:
        user_service = _get_user_service()
        logger.error("/api/user/: _user_service = " + str(user_service))

        if inputs["method"] == "GET":
            rsp = user_service.get_first()

            if rsp is not None:
                rsp_data = rsp
                rsp_status = 200
                rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NONE FOUND"

        elif inputs["method"] == "POST":
            body = inputs.get("body", None)

            if body is None:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "Body Not Received"
            else:
                rsp = user_service.create_user(body)
                rsp_data = rsp
                rsp_status = 200
                rsp_txt = "OK"
        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            full_rsp = Response(json.dumps(rsp_data), status=rsp_status, content_type="application/json")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        log_msg = "/api/user/: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/api/user/", rsp_status, rsp_data, rsp_txt)

    return full_rsp


def etag_match(inputs, rsp):
    headers = inputs.get("headers", None)
    etag = headers.get("Etag", None)
    etags_match = True
    if etag is not None:
        tmp = Response(json.dumps(rsp), status=400, content_type="application/json")
        tmp.add_etag()

        etags_match = werkzeug.http.unquote_etag(etag) == tmp.get_etag()
    return etags_match


@application.route("/api/user/<email>", methods=["GET", "PUT", "DELETE"])
@authorize
def user_email(email):
    global _user_service
    inputs = log_and_extract_input(demo, { "parameters": email })
    rsp_data = None

    try:
        user_service = _get_user_service()
        logger.error("/api/user/email: _user_service = " + str(user_service))

        if inputs["method"] == "GET":
            rsp = user_service.get_by_email(email)
            if rsp is not None:
                rsp_data = rsp
                rsp_status = 200
                rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NOT FOUND"

        elif inputs["method"] == "DELETE":
            rsp = user_service.get_by_email(email)
            if rsp is not None:
                if rsp["status"] == "DELETED":
                    rsp_data = None
                    rsp_status = 404
                    rsp_txt = "User Account " + rsp["email"] + "has already been deleted"
                else:
                    rsp = user_service.delete_user(email)
                    rsp_data = rsp
                    rsp_status = 200
                    rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "USER NOT FOUND"

        elif inputs["method"] == "PUT":
            body = inputs.get("body", None)
            rsp = user_service.get_by_email(email)

            if rsp is not None:
                if rsp["status"] == "DELETED":
                    rsp_data = None
                    rsp_status = 404
                    rsp_txt = "User Account " + rsp["email"] + "is deleted"
                elif body is None:
                    rsp_data = None
                    rsp_status = 404
                    rsp_txt = "Body Not Received"
                elif not etag_match(inputs, rsp):
                    rsp_data = None
                    rsp_status = 404
                    rsp_txt = "ETag did not match, underlying data has changed already."
                else:
                    body["id"] = rsp["id"]
                    rsp = user_service.update_user(body, email)
                    rsp_data = rsp
                    rsp_status = 200
                    rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "USER NOT FOUND"


        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            full_rsp = Response(json.dumps(rsp_data), status=rsp_status, content_type="application/json")
            full_rsp.add_etag()
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        log_msg = "/email: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/email", rsp_status, rsp_data, rsp_txt)

    return full_rsp

@application.route("/api/profile/<profile_entry_id>", methods=["GET", "PUT", "DELETE"])
def profile_profile_entry_id(profile_entry_id):
    global _profile_service
    inputs = log_and_extract_input(demo, { "parameters": profile_entry_id })
    rsp_data = None

    try:
        profile_service = _get_profile_service()
        logger.error("/api/profile/profile_entry_id: _profile_service = " + str(profile_service))

        if inputs["method"] == "GET":
            rsp = profile_service.get_by_profile_entry_id(profile_entry_id)
            if rsp is not None:
                rsp_data = rsp
                rsp_status = 200
                rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NO PROFILE ENTRIES WITH THAT PROFILE ENTRY ID FOUND"

        elif inputs["method"] == "DELETE":
            rsp = profile_service.get_by_profile_entry_id(profile_entry_id)
            if rsp is not None:
                rsp = profile_service.delete_profile_entry(profile_entry_id)
                rsp_data = rsp
                rsp_status = 200
                rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NO PROFILE ENTRIES WITH THAT PROFILE ENTRY ID FOUND TO DELETE"

        elif inputs["method"] == "PUT":
            body = inputs.get("body", None)
            rsp = profile_service.get_by_profile_entry_id(profile_entry_id)
            if rsp is not None:
                if body is None:
                    rsp_data = None
                    rsp_status = 404
                    rsp_txt = "Body Not Received"
                else:
                    # body["id"] = rsp["id"]
                    rsp = profile_service.update_profile_entry(body, profile_entry_id)
                    rsp_data = rsp
                    rsp_status = 200
                    rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "PROFILE ENTRY NOT FOUND"


        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            full_rsp = Response(json.dumps(rsp_data), status=rsp_status, content_type="application/json")
            full_rsp.add_etag()
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        print(e)
        log_msg = "/profile/: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/profile/profile_entry_id", rsp_status, rsp_data, rsp_txt)

    return full_rsp

@application.route("/api/profile/<customer_id>/profile", methods=["GET"])
def profile_customer_id(customer_id):
    global _profile_service
    inputs = log_and_extract_input(demo)
    rsp_data = None
    try:
        profile_service = _get_profile_service()
        logger.error("/api/profile/customer_id/profile: _profile_service = " + str(profile_service))

        if inputs["method"] == "GET":
            rsp = profile_service.get_by_customer_id(customer_id)
            if rsp is not None:
                rsp_data = rsp
                rsp_status = 200
                rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NONE FOUND"

        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            full_rsp = Response(json.dumps(rsp_data), status=rsp_status, content_type="application/json")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")
    except Exception as e:
        log_msg = "/api/profile/: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/api/profile/", rsp_status, rsp_data, rsp_txt)

    return full_rsp


@application.route("/api/profile", methods=["GET", "POST"])
def profile():
    global _profile_service
    inputs = log_and_extract_input(demo)
    rsp_data = None
    try:
        profile_service = _get_profile_service()
        logger.error("/api/profile/: _profile_service = " + str(profile_service))

        if inputs["method"] == "GET":
            queries = inputs['query_params']
            if queries:
                rsp = profile_service.get_queried(queries)
            else:
                rsp = profile_service.get_first()

            if rsp is not None:
                rsp_data = rsp
                rsp_status = 200
                rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NONE FOUND"

        elif inputs["method"] == "POST":
            body = inputs.get("body", None)

            if body is None:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "Body Not Received"
            else:
                rsp = profile_service.create_profile_entry(body)
                rsp_data = rsp
                rsp_status = 200
                rsp_txt = "OK"
        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            full_rsp = Response(json.dumps(rsp_data), status=rsp_status, content_type="application/json")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")
    except Exception as e:
        log_msg = "/api/profile/: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/api/profile/", rsp_status, rsp_data, rsp_txt)

    return full_rsp

@application.route("/api/login", methods=["POST"])
def login():

    inputs = log_and_extract_input(demo, {"parameters": None})
    rsp_data = None
    rsp_status = None
    rsp_txt = None

    try:

        r_svc = _get_registration_service()

        logger.error("/api/login: _r_svc = " + str(r_svc))

        if inputs["method"] == "POST":

            rsp = r_svc.login(inputs['body'])

            if rsp is not None:
                rsp_data = "LOGIN SUCCESSFUL"
                print(rsp)
                rsp_status = 201
                rsp_txt = "CREATED"
            else:
                rsp_data = None
                rsp_status = 403
                rsp_txt = "NOT AUTHORIZED"
        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            headers = {"Authorization": rsp}
            full_rsp = Response(json.dumps(rsp_data, default=str), headers=headers,
                                status=rsp_status, content_type="application/json")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        log_msg = "/api/registration: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/api/registration", rsp_status, rsp_data, rsp_txt)

    return full_rsp

def parse_and_print_args():
    fields=None
    in_args=None
    if request.args is not None:
        in_args=dict(copy.copy(request.args))
        fields=copy.copy(in_args.get('fields',None))
        offset=copy.copy(in_args.get('offset',None))
        limit = copy.copy(in_args.get('limit', None))
        if fields:
            del(in_args['fields'])
        if offset:
            del(in_args['offset'])
        if limit:
            del(in_args['limit'])

    if limit is None:
        limit=10
    else:
        limit=int(limit[0])
    if limit>30:
        limit=30

    if offset is None:
        offset=0
    else:
        offset=int(offset[0])

    try:
        if request.data:
         body=json.loads(request.data)
        else:
         body=None
    except Exception as e:
        print("Got exceptions = ", e)
        body = None


    return in_args, fields, body, offset,limit


@application.route('/api/<resource>', methods=['GET', 'POST'])
@application.route('/api/<resource>/<primary_key>', methods=['GET', 'PUT', 'DELETE'])
@application.route('/api/<resource>/<primary_key>/<related_resource>', methods=['GET', 'POST'])
def get_resource(resource, primary_key =None,related_resource=None):
    in_args, fields, body, offset, limit = parse_and_print_args()

    if request.method=='GET':
        if primary_key is not None:
            if related_resource is not None:
                if related_resource=='career_stats':
                    result = BaseballData.find_career_stats(primary_key)
                    result = BaseballData.add_limit_offset(result, request.path, limit, offset, fields, in_args)
                    return json.dumps(result, indent=2), 200, {"conent-type": "application/json; charset: utf-8"}
                else:
                    result, tmp1 = BaseballData.find_by_related_resource(resource, related_resource, primary_key,in_args, fields)
                    result = BaseballData.add_limit_offset(result, request.path, limit, offset, fields, in_args)
                    return json.dumps(result, indent=2), 200, {"conent-type": "application/json; charset: utf-8"}
            else:
                if resource=='teammates':
                    result=BaseballData.find_teammates(primary_key)
                    result = BaseballData.add_limit_offset(result, request.path, limit, offset, fields, in_args)
                    return json.dumps(result, indent=2), 200, {"conent-type": "application/json; charset: utf-8"}
                else:
                    result,tmp=BaseballData.find_by_primary_key(resource,primary_key,fields)
                    result = BaseballData.add_limit_offset(result, request.path, limit, offset, fields, in_args)
                    return json.dumps(result, indent=2), 200, {"conent-type": "application/json; charset: utf-8"}
        else:
            if resource=='roster':
                result = BaseballData.find_roster(in_args)
                result = BaseballData.add_limit_offset(result, request.path, limit, offset, fields, in_args)
                return json.dumps(result, indent=2), 200, {"conent-type": "application/json; charset: utf-8"}
            else:
                result=BaseballData.find_by_template(resource, in_args, fields)
                result = BaseballData.add_limit_offset(result, request.path, limit, offset,fields, in_args)
                return json.dumps(result, indent=2),200,{"conent-type":"application/json; charset: utf-8"}
    elif request.method=='POST':
        if primary_key is not None:
            result, tmp1 = BaseballData.find_by_related_resource(resource, related_resource, primary_key, in_args, fields)
            tmp1.update(body)

            result = BaseballData.insert(related_resource, tmp1)

            return "Method " + request.method + " on resource " + resource + \
                   " completed successfully ", 201, {"conent-type": "text/plain; charset: utf-8"}
        else:
            result=BaseballData.insert(resource,body)

            return "Method " + request.method + " on resource " + resource + \
                " completed successfully ", 201, {"conent-type":"text/plain; charset: utf-8"}
    elif request.method=='PUT':


        row,tmp = BaseballData.find_by_primary_key(resource, primary_key, None)
        print(row)
        print(body)
        for fld in list(body.keys()):
            row[0][fld]=body[fld]

        del_result=BaseballData.delete(resource,tmp)
        result = BaseballData.insert(resource, row[0])

        return "Method " + request.method + " on resource " + resource + \
               " completed successfully", 201, {"conent-type": "text/plain; charset: utf-8"}

    elif request.method == 'DELETE':

        row, tmp = BaseballData.find_by_primary_key(resource, primary_key, None)
        del_result = BaseballData.delete(resource, tmp)
        return "Method " + request.method + " on resource " + resource + \
               " completed successfully", 201, {"conent-type": "text/plain; charset: utf-8"}

    else:
        return "Method " + request.method + " on resource " + resource + \
               " not implemented!", 501, {"conent-type": "text/plain; charset: utf-8"}



logger.debug("__name__ = " + str(__name__))
# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.

    logger.debug("Starting Project EB at time: " + str(datetime.now()))
    init()

    application.debug = True
    application.run()
