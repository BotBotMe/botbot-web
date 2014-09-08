import json

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

from django.forms import fields
from django.forms.util import ValidationError



class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly"""

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if value == "":
            return None
        try:
            if isinstance(value, basestring):
                return json.loads(value)
        except ValueError:
            pass
        return value

    def get_db_prep_save(self, value, *args, **kwargs):
        if value == "":
            return None

        if value == "{}":
            value = {}

        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value, cls=DjangoJSONEncoder)
            return super(JSONField, self).get_db_prep_save(value, *args, **kwargs)

    def value_from_object(self, obj):
        value = super(JSONField, self).value_from_object(obj)
        if self.null and value is None:
            return None
        return json.dumps(value)

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^botbot\.core\.fields\.JSONField"])
except ImportError:
    pass
