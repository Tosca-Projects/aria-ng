
from ... import make_agnostic
from .writer import Writer
from collections import OrderedDict

class CodeClass(object):
    def __init__(self, generator, name, module=None, base='object', description=None):
        self.generator = generator
        self.name = name
        self.module = module
        self.base = base
        self.description = description
        self.properties = OrderedDict()
        self.methods = OrderedDict()
    
    @property
    def fullname(self):
        return '%s.%s' % (self.module.fullname, self.name)
    
    def make_names_unique(self):
        names = []
        def unique_name(name):
            if name not in names:
                names.append(name)
                return name
            else:
                return unique_name(name + '_')
        
        for m in self.methods.itervalues():
            m.name = unique_name(m.name)
    
    def __str__(self):
        self.make_names_unique()

        with Writer() as w:
            w.write('@has_validated_properties')
            w.write('@has_interfaces')
            base = self.base if isinstance(self.base, str) else (self.base.name if self.base.module == self.module else self.base.fullname)
            w.write('class %s(%s):' % (self.name, base))
            w.i()
            if self.description:
                w.write_docstring(self.description)
            w.write('def __init__(self, context):')
            w.i()
            w.write('self.context = context')
            w.o()
            for n, p in self.properties.iteritems():
                w.write()
                if p.default is not None:
                    w.write('@property_default(%s)' % repr(make_agnostic(p.default)))
                if p.type:
                    w.write('@property_type(%s)' % self.generator.get_classname(p.type))
                w.write('@validated_property')
                w.write('def %s():' % n)
                w.i()
                if p.description or p.type is not None:
                    w.write('"""')
                    if p.description:
                        w.write(p.description.strip())
                    if p.type is not None:
                        if p.description:
                            w.write()
                        w.write(':rtype: :class:`%s`' % self.generator.get_classname(p.type))
                    w.write('"""')
                else:
                    w.write('pass')
                w.o()
            for n, m in self.methods.iteritems():
                w.write()
                w.write(m)
            return str(w)
