from .schema import Schema, SchemaError
from jsonrpc11base.errors import InvalidParamsError, InvalidResultServerError


class Validation(object):
    def __init__(self, schema_dir):
        self.schema = Schema(schema_dir)

    def has_params_validation(self, method_name):
        schema_key = method_name + '.params'
        schema = self.schema.get(schema_key)
        if schema is None:
            return False
        else:
            return schema.get('schema', False)

    def has_absent_params_validation(self, method_name):
        schema_key = method_name + '.params'
        schema = self.schema.get(schema_key)
        if schema is None:
            return False
        else:
            return schema.get('absent', False)

    def has_result_validation(self, method_name):
        schema_key = method_name + '.result'
        if self.schema.get(schema_key) is None:
            return False
        else:
            return True

    def has_absent_result_validation(self, method_name):
        schema_key = method_name + '.result'
        schema = self.schema.get(schema_key)
        if schema is None:
            return False
        else:
            return schema.get('absent', False)

    def validate_params(self, method_name, data):
        schema_key = method_name + '.params'
        try:
            self.schema.validate(schema_key, data)
        except SchemaError as ex:
            raise InvalidParamsError(
                message=ex.message,
                path=ex.path,
                value=ex.value
            )

    def validate_absent_params(self, method_name):
        schema_key = method_name + '.params'
        if self.schema.validate_absent(schema_key) is not True:
            raise InvalidParamsError(
                message='Params must be provided for this method'
            )

    def validate_result(self, method_name, data):
        schema_key = method_name + '.result'
        try:
            self.schema.validate(schema_key, data)
        except SchemaError as ex:
            raise InvalidResultServerError(
                message=ex.message,
                path=ex.path,
                value=ex.value
            )
