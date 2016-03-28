from keyword import iskeyword


class ArgParam:
    '''Class of arguement parameter.
    '''


class OptionParam:
    '''Class of option parameter.
    '''
    def __init__(self, name, alias=None, value=None, formatter=lambda i: i,
                 help='', delimiter=' '):
        self.name = name
        self.alias = alias
        self.formatter = formatter
        self.value = value
        self.help = help
        self.delimiter = delimiter

    @property
    def alias(self):
        return self.__alias

    @alias.setter
    def alias(self, s):
        if s is None:
            s = self.convert_name_to_alias(self.name)
        if s.isidentifier() and not iskeyword(s):
            self.__alias = s
        else:
            raise ValueError('Illegal alias name %s.' % s)

    @staticmethod
    def convert_name_to_alias(s):
        '''Try to convert str to legal Python identifier.'''
        s = s.strip().lstrip('-').replace('-', '_')
        if s[0].isdigit():
            s = '_' + s
        return s

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, v):
        if v is not None:
            v = self.formatter(v)
        self.__value = v

    def __repr__(self):
        # if isinstance(self.value, bool):
        s = '<{}{}{}   "{}">'
        return s.format(self.name, self.delimiter, self.value, self.help)

    def __eq__(self, other):
        ''''''
        return other.name == self.name and other.value == other.value

    def __setattr__(self, n, v):
        '''Override to keep the class attributes immutable.'''
        if n == 'value' or not hasattr(self, n):
            super().__setattr__(n, v)
        else:
            msg = 'Attribute {} of the {} class cannot be changed'
            raise AttributeError(msg.format(n, type(self).__name__))

    def __delattr__(self, *args):
        '''Override to prevent the class attributes from being deleted.'''
        msg = 'Attributes {} of the {} class cannot be deleted'
        raise AttributeError(msg.format(n, type(self).__name__))

    def is_on(self):
        return self.value is None

    def on(self, value):
        self.value = value


class Parameters:
    def __init__(self, params):
        self.params = params

    def __getitem__(self, key):
        return

    def __setitem__(self, key, value):
        self
