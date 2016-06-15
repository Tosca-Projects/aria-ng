
from aria import tosca_specification, has_validated_properties, validated_property, property_type, property_default, required_property
import tosca
    
@has_validated_properties
@tosca_specification('5.7.3')
class Root(object):
    """
    This is the default (root) TOSCA Interface Type definition that all other TOSCA Interface Types derive from.
    
    See the `TOSCA Simple Profile v1.0 specification <http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd02/TOSCA-Simple-Profile-YAML-v1.0-csprd02.html#_Ref384391055>`__ (wrong anchor)
    """
    
MODULES = (
    'node',)

__all__ = (
    'MODULES',
    'Root')
