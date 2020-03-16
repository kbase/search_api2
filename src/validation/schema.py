from jsonschema import validate, RefResolver
from jsonschema.exceptions import ValidationError
import os
import yaml

DEFAULT_SCHEMA_DIR = 'schemas/legacy'


class SchemaError(Exception):
    def __init__(self, message, path, value):
        self.message = message
        self.path = path
        self.value = value


class Schema(object):
    def __init__(self, schema_dir=None, load_schemas=False):
        if schema_dir is not None:
            self.schema_dir = os.path.abspath(schema_dir)
        else:
            self.schema_dir = os.path.abspath(os.path.dirname(__file__) + '/' + DEFAULT_SCHEMA_DIR)

        self.resolver = RefResolver('file://{}/'.format(self.schema_dir), None)

        if load_schemas:
            self.schemas = self.load(self.schema_dir)
        else:
            self.schemas = {}

    def load(self, schema_dir=None):
        schemas = {}
        for file_name in os.listdir(self.schema_dir):
            file_path = os.path.join(self.schema_dir, file_name)
            file_base_name = os.path.splitext(file_name)[0]

            with open(file_path) as f:
                schema = yaml.safe_load(f)
                schemas[file_base_name] = schema
        return schemas

    def validate(self, schema_key, data):
        schema = self.schemas.get(schema_key, None)
        if schema is None:
            raise ValueError('Schema "' + schema_key + '" does not exist')
        try:
            validate(instance=data, schema=schema, resolver=self.resolver)
        except ValidationError as ex:
            message = ex.message
            path = '.'.join(map(str, ex.absolute_schema_path))
            value = ex.validator_value
            raise SchemaError(message, path, value)

    def get(self, schema_name, default_value=None):
        return self.schemas.get(schema_name, default_value)
