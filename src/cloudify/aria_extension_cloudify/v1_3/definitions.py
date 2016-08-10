
from .misc import Description
from .utils.data_types import get_data_type
from aria import dsl_specification
from aria.presentation import Presentation, has_fields, allow_unknown_fields, short_form_field, primitive_field, object_dict_field, object_dict_unknown_fields
from aria.utils import cachedmethod

@has_fields
class PropertyDefinition(Presentation):
    @primitive_field(Description)
    def description(self):
        """
        Description for the property.
        
        :rtype: :class:`Description`
        """

    @primitive_field(str)
    def type(self):
        """
        Property type. Not specifying a data type means the type can be anything (including types not listed in the valid types). Valid types: string, integer, float, boolean or a custom data type.
        
        :rtype: str
        """

    @primitive_field()
    def default(self):
        """
        An optional default value for the property.        
        """

    @primitive_field(bool, default=True)
    def required(self):
        """
        Specifies whether the property is required. (Default: true, Supported since: :code:`cloudify_dsl_1_2`)
        
        :rtype: bool
        """

    @cachedmethod
    def _get_type(self, context):
        return get_data_type(context, self)

@short_form_field('implementation')
@has_fields
class OperationDefinition(Presentation):
    @primitive_field(str)
    def implementation(self):
        """
        The script or plugin task name to execute.
        
        ARIA NOTE: The spec seems to mistakingly mark this as a required field.
        
        :rtype: str
        """

    @object_dict_field(PropertyDefinition)
    def inputs(self):
        """
        Schema of inputs that will be passed to the implementation as kwargs.
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @primitive_field(str)
    def executor(self):
        """
        Valid values: :code:`central_deployment_agent`, :code:`host_agent`.
        
        :rtype: str
        """

    @primitive_field(int)
    def max_retries(self):
        """
        Maximum number of retries for a task. -1 means infinite retries (Default: :code:`task_retries` in manager blueprint Cloudify Manager Type for remote workflows and :code:`task_retries` workflow configuration for local workflows).
        
        :rtype: int
        """

    @primitive_field(int)
    def retry_interval(self):
        """
        Minimum wait time (in seconds) in between task retries (Default: :code:`task_retry_interval` in manager blueprint Cloudify Manager Type for remote workflows and :code:`task_retry_interval` workflow configuration for local workflows).
        
        :rtype: int
        """

@allow_unknown_fields
@has_fields
@dsl_specification('interfaces-1', 'cloudify-1.3')
class InterfaceDefinition(Presentation):
    """
    Interfaces provide a way to map logical tasks to executable operations.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-interfaces/>`__.
    """

    @object_dict_unknown_fields(OperationDefinition)
    def operations(self):
        """
        :rtype: dict of str, :class:`OperationDefinition`
        """
