
from aria import Issue, dsl_specification, import_fullname
from collections import OrderedDict
import re

#
# DataType
#

def coerce_data_type_value(context, presentation, data_type, entry_schema, constraints, value, aspect):
    """
    Handles the \_coerce\_data() hook for complex data types.
    
    There are two kinds of handling:
    
    1. If we have a primitive type as our great ancestor, then we do primitive type coersion, and
       just check for constraints.
       
    2. Otherwise, for normal complex data types we return the assigned property values while making
       sure they are defined in our type. The property definition's default value, if available, will
       be used if we did not assign it. We also make sure that required definitions indeed end up with
       a value.
    """

    primitive_type = data_type._get_primitive_ancestor(context)
    if primitive_type is not None:
        # Must be coercible to primitive ancestor
        value = coerce_to_primitive(context, presentation, primitive_type, constraints, value, aspect)
    else:
        definitions = data_type._get_properties(context)
        if isinstance(value, dict):
            r = OrderedDict()

            # Fill in our values, but make sure they are defined
            for name, v in value.iteritems():
                if name in definitions:
                    definition = definitions[name]
                    definition_type = definition._get_type(context)
                    definition_entry_schema = definition.entry_schema
                    definition_constraints = definition.constraints
                    r[name] = coerce_value(context, presentation, definition_type, definition_entry_schema, definition_constraints, v)
                else:
                    context.validation.report('assignment to undefined property "%s" in type "%s" for "%s"' % (name, data_type._fullname, presentation._fullname), locator=v._locator, level=Issue.BETWEEN_TYPES)

            # Fill in defaults from the definitions, and check if required definitions have not been assigned
            for name, definition in definitions.iteritems():
                if (r.get(name) is None) and hasattr(definition, 'default'):
                    r[name] = definition.default
    
                if getattr(definition, 'required', False) and (r.get(name) is None):
                    context.validation.report('required property "%s" in type "%s" is not assigned a value for "%s"' % (name, data_type._fullname, presentation._fullname), locator=presentation._get_child_locator('definitions'), level=Issue.BETWEEN_TYPES)
            
            value = r
        else:
            context.validation.report('value of type "%s" is not a dict for "%s"' % (data_type._fullname, presentation._fullname), locator=value._locator, level=Issue.BETWEEN_TYPES)
            value = None
    
    return value

#
# PropertyDefinition, AttributeDefinition, EntrySchema
#

def get_data_type(context, presentation, field_name, allow_none=False):
    """
    Returns the type, whether it's a complex data type (a DataType instance) or a primitive (a Python primitive type class).
    
    If the type is not specified, defaults to :class:`str`, per note in section 3.2.1.1 of the
    `TOSCA Simple Profile v1.0 specification <http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd02/TOSCA-Simple-Profile-YAML-v1.0-csprd02.html#_Toc379455072>`__
    """
    
    the_type = getattr(presentation, field_name)
    
    if the_type is None:
        if allow_none:
            return None
        else:
            return str
    
    # Try complex data type
    complex = context.presentation.data_types.get(the_type)
    if complex is not None:
        return complex 
    
    # Try primitive data type
    return get_primitive_data_type(the_type)

#
# ConstraintClause
#

def apply_constraint_to_value(context, presentation, constraint_clause, value):
    """
    Returns false if the value does not conform to the constraint.
    """
    
    constraint_key = constraint_clause._raw.keys()[0]
    the_type = constraint_clause._get_type(context)
    entry_schema = getattr(presentation, 'entry_schema', None) # PropertyAssignment does not have this
    
    def coerce(constraint):
        return coerce_value(context, presentation, the_type, entry_schema, None, constraint, constraint_key)
    
    def report(message, constraint):
        context.validation.report('value %s %s per constraint in "%s": %s' % (message, repr(constraint), presentation._name or presentation._container._name, repr(value)), locator=presentation._locator, level=Issue.BETWEEN_FIELDS)

    if constraint_key == 'equal':
        constraint = coerce(constraint_clause.equal)
        if value != constraint:
            report('is not equal to', constraint)
            return False

    elif constraint_key == 'greater_than':
        constraint = coerce(constraint_clause.greater_than)
        if value <= constraint:
            report('is not greater than', constraint)
            return False

    elif constraint_key == 'greater_or_equal':
        constraint = coerce(constraint_clause.greater_or_equal)
        if value < constraint:
            report('is not greater than or equal to', constraint)
            return False

    elif constraint_key == 'less_than':
        constraint = coerce(constraint_clause.less_than)
        if value >= constraint:
            report('is not less than', constraint)
            return False

    elif constraint_key == 'less_or_equal':
        constraint = coerce(constraint_clause.less_or_equal)
        if value > constraint:
            report('is not less than or equal to', constraint)
            return False

    elif constraint_key == 'in_range':
        lower, upper = constraint_clause.in_range
        lower, upper = coerce(lower), coerce(upper)
        if value < lower:
            report('is not greater than or equal to lower bound', lower)
            return False
        if (upper != 'UNBOUNDED') and (value > upper):
            report('is not lesser than or equal to upper bound', upper)
            return False

    elif constraint_key == 'valid_values':
        constraint = (coerce(v) for v in constraint_clause.valid_values)
        if value not in constraint:
            report('is not one of', constraint)
            return False

    elif constraint_key == 'length':
        constraint = constraint_clause.length
        try:
            if len(value) != constraint:
                report('is not of length', constraint)
                return False
        except TypeError:
            pass # should be validated elsewhere

    elif constraint_key == 'min_length':
        constraint = constraint_clause.min_length
        try:
            if len(value) < constraint:
                report('has a length lesser than', constraint)
                return False
        except TypeError:
            pass # should be validated elsewhere

    elif constraint_key == 'max_length':
        constraint = constraint_clause.max_length
        try:
            if len(value) > constraint:
                report('has a length greater than', constraint)
                return False
        except TypeError:
            pass # should be validated elsewhere

    elif constraint_key == 'pattern':
        constraint = constraint_clause.pattern
        try:
            # Note: the TOSCA 1.0 spec does not specify the regular expression grammar, so we will just use Python's
            if re.match(constraint, str(value)) is None:
                report('does not match regular expression', constraint)
                return False
        except re.error:
            pass # should be validated elsewhere
    
    return True

#
# Utils
#

PRIMITIVE_DATA_TYPES = {
    # YAML 1.2:
    'tag:yaml.org,2002:str': str,
    'tag:yaml.org,2002:integer': int,
    'tag:yaml.org,2002:float': float,
    'tag:yaml.org,2002:bool': bool,
    'tag:yaml.org,2002:null': None.__class__,

    # TOSCA aliases:
    'string': str,
    'integer': int,
    'float': float,
    'boolean': bool,
    'null': None.__class__}

@dsl_specification('3.2.1', 'tosca-simple-profile-1.0')
def get_primitive_data_type(type_name):
    """
    Many of the types we use in this profile are built-in types from the YAML 1.2 specification (i.e., those identified by the "tag:yaml.org,2002" version tag) [YAML-1.2].
    
    See the `TOSCA Simple Profile v1.0 specification <http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd02/TOSCA-Simple-Profile-YAML-v1.0-csprd02.html#_Toc373867862>`__
    """
    
    return PRIMITIVE_DATA_TYPES.get(type_name)

def get_data_type_name(the_type):
    """
    Returns the name of the type, whether it's a DataType, a primitive type, or another class.
    """
    
    if hasattr(the_type, '_name'):
        return the_type._name
    return '%s.%s' % (the_type.__module__, the_type.__name__) 

def coerce_value(context, presentation, the_type, entry_schema, constraints, value, aspect=None):
    """
    Returns the value after it's coerced to its type, reporting validation errors if it cannot be coerced.
    
    Supports both complex data types and primitives.
    
    Data types can use the "coerce\_value" extension to hook their own specialized function. If the extension
    is present, we will delegate to that hook.
    """
    
    if the_type is None:
        return None

    if the_type == None.__class__:
        if value is not None:
            context.validation.report('field "%s" is of type "null" but has a non-null value: %s' % (presentation._name, repr(value)), locator=presentation._locator, level=Issue.BETWEEN_FIELDS)
            return None
    
    # Delegate to 'coerce_value' extension
    if hasattr(the_type, '_get_extension'):
        coerce_value_fn_name = the_type._get_extension('coerce_value')
        if coerce_value_fn_name is not None:
            coerce_value_fn = import_fullname(coerce_value_fn_name)
            return coerce_value_fn(context, presentation, the_type, entry_schema, constraints, value, aspect)

    if hasattr(the_type, '_coerce_value'):
        # Delegate to type (likely a DataType instance)
        return the_type._coerce_value(context, presentation, entry_schema, constraints, value, aspect)

    if the_type is not None:
        # Coerce to primitive type
        return coerce_to_primitive(context, presentation, the_type, constraints, value, aspect)
    
    return None

def apply_constraints_to_value(context, presentation, constraints, value):
    if (value is not None) and (constraints is not None):
        valid = True
        for constraint in constraints:
            if not constraint._apply_to_value(context, presentation, value):
                valid = False
        if not valid:
            value = None
    return value

def coerce_to_primitive(context, presentation, primitive_type, constraints, value, aspect=None):
    try:
        # Coerce
        value = primitive_type(value)
        
        # Check constraints
        apply_constraints_to_value(context, presentation, constraints, value)
    except ValueError as e:
        report_issue_for_bad_format(context, presentation, primitive_type, value, aspect, e)
        value = None
    except TypeError as e:
        report_issue_for_bad_format(context, presentation, primitive_type, value, aspect, e)
        value = None
    
    return value

def coerce_to_class(context, presentation, the_type, entry_schema, constraints, value, aspect=None):
    try:
        value = the_type(entry_schema, constraints, value, aspect)
    except ValueError as e:
        report_issue_for_bad_format(context, presentation, the_type, value, aspect, e)
        value = None
    
    # Check constraints
    apply_constraints_to_value(context, presentation, constraints, value)
        
    return value

def report_issue_for_bad_format(context, presentation, the_type, value, aspect, e):
    aspect = None
    if aspect == 'default':
        aspect = '"default" value'
    elif aspect is not None:
        aspect = '"%s" constraint'  
    
    if aspect is not None:
        context.validation.report('%s for field "%s" is not a valid "%s": %s' % (aspect, presentation._name or presentation._container._name, get_data_type_name(the_type), repr(value)), locator=presentation._locator, level=Issue.BETWEEN_FIELDS, exception=e)
    else:
        context.validation.report('field "%s" is not a valid "%s": %s' % (presentation._name or presentation._container._name, get_data_type_name(the_type), repr(value)), locator=presentation._locator, level=Issue.BETWEEN_FIELDS, exception=e)
