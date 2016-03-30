from keyword import iskeyword
from tempfile import mkdtemp
from collections import OrderedDict
from collections.abc import Mapping
from subprocess import Popen, DEVNULL


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


class Param:
    def __init__(self, name, value=None, formatter=lambda i: i, help=''):
        self.name = name
        self.formatter = formatter
        self.value = value
        self.help = help

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, v):
        if v is not None:
            v = self.formatter(v)
        self.__value = v

    def on(self, value):
        self.value = value
        return self

    def off(self):
        self.value = None
        return self

    def is_on(self):
        return not self.is_off()

    def is_off(self):
        return self.value is False or self.value is None

    def __str__(self):
        if self.is_off():
            return ''
        else:
            return self.value


class ArgmntParam(Param):
    '''Class of argument parameter.
    '''

    def __repr__(self):
        # if isinstance(self.value, bool):
        s = '{}(name="{}", value={}, formatter={}, help="{}")'
        return s.format(self.__class__.__name__,
                        self.name, self.value, self.formatter.__name__,
                        self.help)


class OptionParam(Param):
    '''Class of option parameter.

    Parameters
    ----------
    formatter : callable
        To validate and tokenize the `value` into right format.
        For example, if `value` is a file path, use `shlex.quote`.
    '''
    def __init__(self, name, alias=None, value=None, formatter=lambda i: i,
                 help='', delimiter=' '):
        super().__init__(name, value, formatter, help)
        self.alias = alias
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

    def __repr__(self):
        # if isinstance(self.value, bool):
        s = '{}(name="{}", alias="{}", value={}, formatter={}, help="{}", delimiter="{}")'
        return s.format(self.__class__.__name__,
                        self.name, self.alias, self.value, self.formatter.__name__,
                        self.help, self.delimiter)

    def __str__(self):
        if self.is_off():
            return ''
        elif self.value is True:
            return self.name
        else:
            return '{}{}{}'.format(self.name, self.delimiter, self.value)

    def __eq__(self, other):
        ''''''
        return other.name == self.name and other.value == self.value

    def is_on(self):
        return not self.is_off()

    def is_off(self):
        return self.value is False or self.value is None


class Parameters(Mapping):
    def __init__(self, *args, **kwargs):
        self._data = OrderedDict(*args, **kwargs)
        self._alias_map = {}
        for k in self._data:
            p = self._data[k]
            if isinstance(p, OptionParam):
                self._alias_map[p.alias] = p.name

    @classmethod
    def from_params(cls, params):
        k_v_it = ((param.name, param) for param in params)
        return cls(k_v_it)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data or key in self._alias_map

    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        elif key in self._alias_map:
            return self._data[self._alias_map[key]]
        else:
            raise KeyError(key)

    def __setitem__(self, k, v):
        if k in self:
            self[k].on(v)
        else:
            msg = 'You cannot set value {} on key {}'
            raise ValueError(msg.format(v, k))

    def update(self, **kwargs):
        for k in kwargs:
            self[k].on(kwargs[k])

    def off(self):
        for k in self._data:
            self[k].off()

    def __repr__(self):
        items = []
        for k in self._data:
            items.append(repr(self._data[k]))
        return '\n'.join(items)


class Dumpling:
    def __init__(self, cmd, params,
                 stdin=None, stdout=None, stderr=None,
                 cwd=None, tmp_dir=None,
                 version='', url=''):
        if isinstance(cmd, str):
            cmd = [cmd]
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr
        self.stdin = stdin
        if tmp_dir is None:
            tmp_dir = mkdtemp()
        self.tmp_dir = tmp_dir
        self.cwd = cwd
        self.params = params
        self.version = version
        self.url = url

    @property
    def command(self):
        command = []
        command.extend(self.cmd)
        for k in self.params:
            p = self.params[k]
            arg = str(p)
            if arg:
                command.append(arg)
        return ' '.join(command)

    def __call__(self, **kwargs):
        ''''''
        self.params.update(**kwargs)
        print(self.command)
        p = Popen(self.command, cwd=self.cwd, shell=True,
                  stdin=self.stdin, stdout=self.stdout, stderr=self.stderr)
        p.wait()
        return p
