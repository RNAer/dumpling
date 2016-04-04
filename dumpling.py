from keyword import iskeyword
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from collections import OrderedDict
from collections.abc import Mapping
from subprocess import Popen
from copy import deepcopy


__version__ = '0.1.2'


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
    def __init__(self, name, value=None, action=lambda i: i, help=''):
        self.name = name
        self.action = action
        self.value = value
        self.help = help

    @property
    def value(self):
        '''The value of the parameter.'''
        return self.__value

    @value.setter
    def value(self, v):
        if v is not None:
            v = self.action(v)
        self.__value = v

    def on(self, value):
        '''Set the value of the parameter.'''
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

    def __eq__(self, other):
        ''''''
        return other.name == self.name and other.value == self.value


class ArgmntParam(Param):
    '''Class of argument parameter.
    '''

    def __repr__(self):
        # if isinstance(self.value, bool):
        s = '{}(name={!r}, value={!r}, action={}, help={!r})'
        return s.format(self.__class__.__name__, self.name, self.value,
                        self.action.__name__, self.help)

    def _get_arg(self):
        if self.is_on():
            return [str(self.value)]
        else:
            return []


class OptionParam(Param):
    '''Class of option parameter.

    Parameters
    ----------
    action : callable
        To validate and tokenize the `value` into right format.
        For example, if `value` is a file path, use `shlex.quote`.
    '''
    def __init__(self, name, alias=None, value=None, action=lambda i: i,
                 help='', delimiter=' '):
        super().__init__(name, value, action, help)
        self.alias = alias
        self.delimiter = delimiter

    @property
    def alias(self):
        '''The alias for parameter.'''
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
        return s

    def __repr__(self):
        # if isinstance(self.value, bool):
        s = '{}(name={!r}, alias={!r}, value={!r}, action={}, help={!r}, delimiter={!r})'
        return s.format(self.__class__.__name__, self.name, self.alias, self.value,
                        self.action.__name__, self.help, self.delimiter)

    def __str__(self):
        if self.is_off():
            return ''
        elif self.value is True:
            return self.name
        else:
            return '{}{}{}'.format(self.name, self.delimiter, self.value)

    def _get_arg(self):
        if self.is_on():
            if self.delimiter.isspace():
                return [self.name, str(self.value)]
            else:
                return ['{}{}{}'.format(self.name, self.delimiter, self.value)]
        else:
            return []


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
        '''Construct an instance from a list of OptionParam or ArgmntParam.'''
        # create a copy of each param
        k_v_it = ((param.name, deepcopy(param)) for param in params)
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
            msg = 'You cannot set value {!r} on unknown key {!r}'
            raise ValueError(msg.format(v, k))

    def update(self, **kwargs):
        '''Update the parameter values.'''
        for k in kwargs:
            self[k] = kwargs[k]

    def off(self):
        '''Turn off all the parameters.'''
        for k in self._data:
            self[k].off()

    def __repr__(self):
        items = []
        for k in self._data:
            items.append(repr(self._data[k]))
        return '\n'.join(items)


class Dumpling:
    def __init__(self, cmd, params, version='', url=''):
        if isinstance(cmd, str):
            cmd = [cmd]
        self.cmd = cmd
        self.params = deepcopy(params)
        self.version = version
        self.url = url

    @property
    def command(self):
        command = []
        command.extend(self.cmd)
        for k in self.params:
            p = self.params[k]
            command.extend(p._get_arg())
        return command

    def __repr__(self):
        items = []
        name = self.__class__.__name__
        items.append(name)
        items.append('-' * len(name))
        items.append('CMD: {}'.format(' '.join(self.cmd)))
        items.append('CMD version: {!r}'.format(self.version))
        items.append('CMD URL: {!r}'.format(self.url))
        items.append('CMD Parameter:\n{!r}'.format(self.params))
        return '\n'.join(items)

    def __str__(self):
        return ' '.join(self.command)

    def update(self, **kwargs):
        self.params.update(**kwargs)

    @contextmanager
    def __call__(self, cwd=None, stdin=None, stdout=None, stderr=None,
                 **kwargs):
        '''
        Parameters
        ----------
        cwd : str
            working dir
        stdin : str
            file to provide stdin
        stdout, stderr : str or `subprocess.DEVNULL`
            file to store output.

        Yield
        -----
        tuple: int, file object (or `subprocess.DEVNULL`), file object (or `subprocess.DEVNULL`)
        '''
        p = deepcopy(self.params)
        self.params.update(**kwargs)
        if stdout is None:
            stdout = NamedTemporaryFile('w+')
        elif isinstance(stdout, str):
            stdout = open(stdout, 'w+')
        if stderr is None:
            stderr = NamedTemporaryFile('w+')
        elif isinstance(stderr, str):
            stderr = open(stderr, 'w+')
        if isinstance(stdin, str):
            stdin = open(stdin, 'r')

        proc = Popen(self.command, cwd=cwd, shell=False,
                     stdin=stdin, stdout=stdout, stderr=stderr)
        proc.wait()
        for f in [stdout, stderr]:
            try:
                f.seek(0)
            except AttributeError:
                pass

        yield proc.returncode, stdout, stderr

        # reset parameters
        self.params = p
        for f in [stdout, stderr, stdin]:
            try:
                f.close()
            except AttributeError:
                pass
