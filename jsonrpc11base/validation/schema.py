from jsonschema import validate, RefResolver
from jsonschema.exceptions import ValidationError
import os
import glob
import json

DEFAULT_SCHEMA_DIR = 'schemas'


class SchemaError(Exception):
    def __init__(self, message, path, value):
        self.message = message
        self.path = path
        self.value = value


class Schema(object):
    def __init__(self, schema_dir):
        if schema_dir is None:
            raise Exception('schema_dir is required')

        self.schema_dir = os.path.abspath(schema_dir)

        self.resolver = RefResolver(f'file://{schema_dir}/', None)

        self.schemas = self.load()

    def load(self):
        schemas = {}
        for file_path in glob.glob(f'{self.schema_dir}/*.json'):
            file_base_name = os.path.splitext(os.path.basename(file_path))[0]

            with open(file_path) as fd:
                schema_text = fd.read()
                if len(schema_text) == 0:
                    # this means the associated value must
                    # be absent
                    schema = {
                        'absent': True
                    }
                else:
                    schema = {
                        'schema': json.loads(schema_text)
                    }
                schemas[file_base_name] = schema
        return schemas

    def validate_absent(self, schema_key):
        """ Used in the case in which the value is absent. """
        schema = self.schemas.get(schema_key, None)
        if schema is None:
            return False
        return schema.get('absent', False)

    def validate(self, schema_key, value):
        schema_wrapper = self.schemas.get(schema_key)

        if schema_wrapper is None:
            raise SchemaError(
                f'Schema "{schema_key}" does not exist',
                '',
                value
            )

        if schema_wrapper.get('absent') is True:
            raise SchemaError(
                f'Schema "{schema_key}" specifies the the value must be absent',
                '',
                value
            )

        schema = schema_wrapper.get('schema')
        try:
            validate(instance=value, schema=schema, resolver=self.resolver)
        except ValidationError as ex:
            message = ex.message
            path = '.'.join(map(str, ex.absolute_schema_path))
            raise SchemaError(message, path, ex.validator_value)

    def get(self, schema_name, default_value=None):
        return self.schemas.get(schema_name, default_value)
