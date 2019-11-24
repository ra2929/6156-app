import DataAccess.DataAdaptor as data_adaptor
from abc import ABC, abstractmethod
import pymysql.err


class DataException(Exception):
    unknown_error   =   1001
    duplicate_key   =   1002

    def __init__(self, code=unknown_error, msg="Something awful happened."):
        self.code = code
        self.msg = msg


class BaseDataObject(ABC):
    def __init__(self):
        pass

    @classmethod
    @abstractmethod
    def create_instance(cls, data):
        pass

class ProfilesRDB(BaseDataObject):

    def __init__(self, ctx):
        super().__init__()

        self._ctx = ctx

    @classmethod
    def get_first(cls):
        sql = "select * from e6156.profile_entries limit 1"
        res, data = data_adaptor.run_q(sql=sql, fetch=True)
        if data is not None and len(data) > 0:
            result = data[0]
        else:
            result = None

        return result

    @classmethod
    def get_queried(cls,queries):
        supported_queries = ['customer_id','type','subtype','value']
        queryList = []
        for k,v in queries.items():
            if k in supported_queries:
                queryList.append("%s='%s'"%(k,v))
        if queryList:
            sql = "select * from e6156.profile_entries where " + " AND ".join(queryList)
        else:
            sql = "select * from e6156.profile_entries"
        print(sql)
        res, data = data_adaptor.run_q(sql=sql, fetch=True)
        if data is not None and len(data) > 0:
            result = data[:100] #maximum 100 results for a given query
        else:
            result = None

        return result

    @classmethod
    def create_profile_entry(cls, profile_entry_info):

        result = None

        try:
            sql, args = data_adaptor.create_insert(table_name="e6156.profile_entries", row=profile_entry_info)
            res, data = data_adaptor.run_q(sql, args)
            if res != 1:
                result = None
            else:
                result = profile_entry_info['profile_entry_id']
        except pymysql.err.IntegrityError as ie:
            if ie.args[0] == 1062:
                raise (DataException(DataException.duplicate_key))
            else:
                raise DataException()
        except Exception as e:
            raise DataException()

        return result

    @classmethod
    def get_by_profile_entry_id(cls, profile_entry_id):
        sql = "select * from e6156.profile_entries where profile_entry_id=%s"
        res, data = data_adaptor.run_q(sql=sql, args=(profile_entry_id), fetch=True)
        if data is not None and len(data) > 0:
            result = data[0]
        else:
            result = None

        return result


    @classmethod
    def get_by_customer_id(cls, customer_id):
        sql = "select * from e6156.profile_entries where customer_id=%s"
        res, data = data_adaptor.run_q(sql=sql, args=(customer_id), fetch=True)
        if data is not None and len(data) > 0:
            result = data
        else:
            result = None

        return result

    @classmethod
    def delete_profile_entry(cls, profile_entry_id):
        sql = "delete from e6156.profile_entries where profile_entry_id=%s"
        res, data = data_adaptor.run_q(sql=sql, args=(profile_entry_id), fetch=True)
        if data is not None:
            result = data
        else:
            result = None

        return result

    @classmethod
    def update_profile_entry(cls, profile_entry_id, body):

        result = None

        try:
            sql, args = data_adaptor.create_update(table_name="e6156.profile_entries", new_values=body, template={"profile_entry_id":profile_entry_id})
            # sql, args = data_adaptor.create_insert(table_name="users", row=user_info)
            res, data = data_adaptor.run_q(sql, args)
            result = profile_entry_id
        except pymysql.err.IntegrityError as ie:
            if ie.args[0] == 1062:
                raise (DataException(DataException.duplicate_key))
            else:
                raise DataException()
        except Exception as e:
            raise DataException()

        return result




class UsersRDB(BaseDataObject):

    def __init__(self, ctx):
        super().__init__()

        self._ctx = ctx

    @classmethod
    def get_first(cls):
        sql = "select * from e6156.users limit 1"
        res, data = data_adaptor.run_q(sql=sql, fetch=True)
        if data is not None and len(data) > 0:
            result = data[0]
        else:
            result = None

        return result

    @classmethod
    def get_by_email(cls, email):
        sql = "select * from e6156.users where email=%s"
        res, data = data_adaptor.run_q(sql=sql, args=(email), fetch=True)
        if data is not None and len(data) > 0:
            result = data[0]
        else:
            result = None

        return result

    @classmethod
    def delete_user(cls, email):
        sql = "UPDATE e6156.users SET status = 'DELETED' WHERE email=%s"
        res, data = data_adaptor.run_q(sql=sql, args=(email), fetch=True)
        if data is not None and len(data) > 0:
            result = data[0]
        else:
            result = None

        return result

    @classmethod
    def create_user(cls, user_info):

        result = None

        try:
            sql, args = data_adaptor.create_insert(table_name="e6156.users", row=user_info)
            res, data = data_adaptor.run_q(sql, args)
            if res != 1:
                result = None
            else:
                result = user_info['id']
        except pymysql.err.IntegrityError as ie:
            if ie.args[0] == 1062:
                raise (DataException(DataException.duplicate_key))
            else:
                raise DataException()
        except Exception as e:
            raise DataException()

        return result

    @classmethod
    def update_user(cls, email, user_info):

        result = None

        try:
            sql, args = data_adaptor.create_update(table_name="e6156.users", new_values=user_info, template={"email":email})
            # sql, args = data_adaptor.create_insert(table_name="users", row=user_info)
            res, data = data_adaptor.run_q(sql, args)
            if res != 1:
                result = None
            else:
                result = user_info['id']
        except pymysql.err.IntegrityError as ie:
            if ie.args[0] == 1062:
                raise (DataException(DataException.duplicate_key))
            else:
                raise DataException()
        except Exception as e:
            raise DataException()

        return result




