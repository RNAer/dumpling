from keyword import iskeyword
from collections import OrderedDict


def check_choice(it):
    def func(v):
        if v not in it:
            msg = 'Illegal value: {}'
            raise ValueError(msg.format(v))
        return v
    return func


def check_range(minimum, maximum):
    def func(v):
        if not minimum < v < maximum:
            msg = 'Illegal value: {}'
            raise ValueError(msg.format(v))
        return v
    return func


class ArgmntParam:
    '''Class of arguement parameter.
    '''


class OptionParam:
    '''Class of option parameter.

    Parameters
    ----------
    formatter : callable
        To validate and tokenize the `value` into right format.
        For example, if `value` is a file path, use `shlex.quote`.
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

    def __str__(self):
        if self.value is False or self.value is None:
            return ''
        elif self.value is True:
            return self.name
        else:
            return '{}{}{}'.format(self.name, self.delimiter, self.value)

    def __eq__(self, other):
        ''''''
        return other.name == self.name and other.value == self.value

    def is_on(self):
        return self.value is not None

    def on(self, value):
        self.value = value


class Parameters(OrderedDict):
    @classmethod
    def from_params(cls, params):
        return cls(yield from [(param.name, param), (param.alias, param)]
                   for param in params)

    def __setitem__(self, name, value):
        self[name].on(value)
        self[self.alias_map[name]].on(value)

    def __getitem__(self, name):
        if name in self:
            return self[name]
        elif self[self.alias_map[name]] in self:
            return self[self.alias_map[name]]

    def __repr__(self):
        ''''''


class Dumpling:
    def __init__(self, cmd, params,
                 cwd, tmp_dir,
                 stdin, stdout, stderr,
                 cmd_delimiter=' ',
                 version='', url=''):
        self.version = version

    @property
    def command(self):
        return

    def __call__(**kwargs):
        ''''''

    def __str__(self):
        ''''''
        items = []
        for k in self.params:
            p = self.params[k]
            s = str(s)
            if s:
                items.append(s)
        return self.delimiter.join(items)
