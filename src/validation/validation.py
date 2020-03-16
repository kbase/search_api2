from .schema import Schema, SchemaError
import src.jsonrpcbase as jsonrpcbase

# class JSONRPCError(Exception):
#     def __init__(self, code=None, message=None, data=None):
#         self.code = getattr(self.__class__, "CODE", code)
#         self.message = getattr(self.__class__, "MESSAGE", message)
#         self.data = data

#     def to_json(self):
#         if self.code is None:
#             raise Exception('Error Error - missing code')

#         if self.message is None:
#             raise Exception('Error Error - missing message')

#         return {
#             'version': '1.1',
#             'id': '1234',
#             'error': {
#                 'code': self.code,
#                 'message': self.message,
#                 'data': self.data
#             }
#         }


# class InvalidParamsError(JSONRPCError):
#     CODE = -32602
#     MESSAGE = "Invalid params"


class Validation(object):
    def __init__(self, load_schemas=False):
        self.schema = Schema(load_schemas=load_schemas)

    def has_param_validation(self, method_name):
        schema_key = method_name + '.params'
        if self.schema.get(schema_key) is None:
            return False
        else:
            return True

    def has_result_validation(self, method_name):
        schema_key = method_name + '.result'
        if self.schema.get(schema_key) is None:
            return False
        else:
            return True

    def validate_params(self, method_name, data):
        schema_key = method_name + '.params'
        try:
            self.schema.validate(schema_key, data)
        except SchemaError as ex:
            raise jsonrpcbase.InvalidParamsError(data={
                'schema_error': ex.message,
                'schema_path': ex.path,
                'schema_value': ex.value
            })

    def validate_result(self, method_name, data):
        schema_key = method_name + '.result'
        try:
            self.schema.validate(schema_key, data)
        except SchemaError as ex:
            raise jsonrpcbase.InvalidResultError(data={
                'schema_error': ex.message,
                'schema_path': ex.path,
                'schema_value': ex.value
            })

    def validate_config(self, data):
        schema_key = 'config'
        try:
            self.schema.validate(schema_key, data)
        except SchemaError as ex:
            raise jsonrpcbase.InvalidParamsError(data={
                'schema_error':  ex.message,
                'schema_path': ex.path,
                'schema_value': ex.value
            })
