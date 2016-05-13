from keyword import iskeyword
from collections import OrderedDict
from collections.abc import Mapping
from abc import ABC, abstractmethod
from subprocess import run, PIPE
from copy import deepcopy


__version__ = '0.1.3'


def check_choice(it):
    '''return a function to check the value is a choice of a list of legal values.

    Parameters
    ----------
    it : `Iterable`
        A set of all legal values.

    Returns
    -------
    function
        A function that receive the value, does the checking, and return the value
        if it is legal.

    Examples
    --------
    >>> from dumpling import check_choice
    >>> f = check_choice(('fna', 'fasta', 'faa'))
    >>> f('fna')
    'fna'
    >>> f('abc')   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
        raise ValueError(msg.format(v))
    ValueError: Illegal value: abc

    '''
    def func(v):
        '''check value.

        Parameters
        ----------
        v : arbitrary

        Returns
        -------
        v
            The input value.

        Raises
        ------
        ValueError
            If the given value of `v` is not a choice from the list of legal values.
        '''
        if v not in it:
            msg = 'Illegal value: {}'
            raise ValueError(msg.format(v))
        return v
    return func


def check_range(minimum, maximum):
    '''return a function to check the value is in the legal range.

    Parameters
    ----------
    minimum : `Numeric`
        the lower bound
    maximum : `Numeric`
        the upper bound

    Returns
    -------
    function
        A function that receive the value and does the checking, and return the value
        if it is legal.

    Examples
    --------
    >>> from dumpling import check_range
    >>> f = check_range(0, 9)
    >>> f('2')
    '2'
    >>> f('10')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
        raise ValueError(msg.format(v))
    ValueError: Illegal value: 10
    '''
    def func(v):
        '''check value.

        Parameters
        ----------
        v : `Numeric`

        Returns
        -------
        v
            The input value.

        Raises
        ------
        ValueError
            If the given value of `v` is not inside the (mininum, maximum).
        '''
        v_ = float(v)
        if not minimum <= v_ <= maximum:
            msg = 'Illegal value: {}'
            raise ValueError(msg.format(v))
        return v
    return func


class Param(ABC):
    '''Abstract base class for command line parameters.

    '''
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
        '''Turn off the parameter by setting value to `None`.'''
        self.value = None
        return self

    def is_on(self):
        '''Return True if the parameter is on.

        Otherwise, return False.'''
        return not self.is_off()

    def is_off(self):
        '''Return True if the parameter is off.

        Otherwise, return False.'''
        return self.value is False or self.value is None

    @abstractmethod
    def __str__(self):
        '''str() method.'''

    @abstractmethod
    def __repr__(self):
        '''repr() method.'''

    @abstractmethod
    def _get_arg(self):
        '''Return the parameter as list.'''

    def __eq__(self, other):
        '''Compare two parameters.'''
        return other.value == self.value


class ArgmntParam(Param):
    '''Class of command line argument parameter.

    Parameters
    ----------
    name : str
        The parameter name.
    value : arbitrary
        The value for the parameter (default is `None`). If the value is a
        string of file or directory path, users don't need to add extra quotes
        because it passes to `subprocess.Popen`.
    action : callable
        The callable to operate on the value to do validation, formatting,
        etc. The default callable is to return the value itself without doing
        anything. See `check_choice` and `check_range`.
    help : str
        The help or description message for the parameter.

    Attributes
    ----------
    name
    action
    value
    help

    Examples
    --------
    >>> from dumpling import ArgmntParam
    >>> def end_with_dmnd(s):
    ...     if s.endswith('.dmnd'):
    ...         return s[:-5]
    ...     else:
    ...         raise ValueError('Wrong input')
    ...
    >>> p = ArgmntParam('db', 'DNase.dmnd', end_with_dmnd, 'input Diamond db file')
    >>> p.value
    'DNase'
    >>> p.off()
    ArgmntParam(name='db', value=None, action=end_with_dmnd, help='input Diamond db file')
    >>> str(p)
    ''
    >>> p = ArgmntParam('db', 'DNase', end_with_dmnd, 'input Diamond db file')
    Traceback (most recent call last):
     ...
    ValueError: Wrong input
    '''
    def __str__(self):
        '''Return the string of the parameter value.'''
        if self.is_off():
            return ''
        else:
            return str(self.value)

    def __repr__(self):
        '''Return the string representation of the argument parameter.'''
        # if isinstance(self.value, bool):
        s = '{}(name={!r}, value={!r}, action={}, help={!r})'
        return s.format(self.__class__.__name__, self.name, self.value,
                        self.action.__name__, self.help)

    def _get_arg(self):
        '''Return the parameter as list.'''
        if self.is_on():
            return [str(self.value)]
        else:
            return []


class OptionParam(Param):
    '''Class of option parameter.

    Parameters
    ----------
    flag : str
        The parameter flag, i.e. the flag of the parmeter, e.g., "--force"
    alter: str
        The alternative parameter flag, e.g., "-f"
    name : str or `None` (default)
        If it is `None`, it will try to automatically infer name from the flag
        by removing the beginning "-" and replace "-" with "_".
    value : arbitrary
        The value for the parameter (default is `None`). If the value is a
        string of file or directory path, users don't need to add extra quotes
        because it passes to `subprocess.Popen`.
    aciton : callable
        The callable to operate of the value to do validation, formatting,
        etc. The default callable is to return the value itself without doing
        anything. See `check_choice` and `check_range`.
    help : str
        The help or description message for the parameter.
    delimiter : str
        The delimiter to combine the flag and the value of the parameter.

    Attributes
    ----------
    flag
    alter
    name
    value
    action
    help
    delimiter

    Examples
    --------
    >>> from dumpling import OptionParam
    >>> p = OptionParam('-i', '--input', value='input.txt', help='input file path')
    >>> p
    OptionParam(flag='-i', alter='--input', name='i', value='input.txt', action=<lambda>, help='input file path', delimiter=' ')
    >>> p.name
    'i'
    >>> str(p)
    '-i input.txt'
    >>> p = OptionParam('--input', '-i', value='input.txt', help='input file path', delimiter='=')
    >>> p.is_on()
    True
    >>> str(p)
    '--input=input.txt'
    >>> p.off()
    OptionParam(flag='--input', alter='-i', name='input', value=None, action=<lambda>, help='input file path', delimiter='=')
    >>> str(p)
    ''
    >>> # "-1" can not be automatically convert to a legal python identifier for the attribute `name`.
    >>> p = OptionParam('-1', value='input.txt', help='input file path')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
        raise ValueError('Illegal alias name %s.' % s)
    ValueError: Illegal alias name 1.
    '''
    def __init__(self, flag, alter=None, name=None, value=None, action=lambda i: i,
                 help='', delimiter=' '):
        self.flag = flag
        self.alter = alter
        self.name = name
        self.action = action
        self.value = value
        self.help = help
        self.delimiter = delimiter

    @property
    def name(self):
        '''The name for parameter.'''
        return self.__name

    @name.setter
    def name(self, s):
        if s is None:
            s = self.convert_flag_to_name(self.flag)
        if s.isidentifier() and not iskeyword(s):
            self.__name = s
        else:
            raise ValueError('Illegal alias name %s.' % s)

    @staticmethod
    def convert_flag_to_name(s):
        '''Try to convert str to legal Python identifier.'''
        s = s.strip().lstrip('-').replace('-', '_')
        return s

    def __repr__(self):
        '''Return the string representation of the option parameter.'''
        # if isinstance(self.value, bool):
        s = '{}(flag={!r}, alter={!r}, name={!r}, value={!r}, action={}, help={!r}, delimiter={!r})'
        return s.format(self.__class__.__name__, self.flag, self.alter, self.name, self.value,
                        self.action.__name__, self.help, self.delimiter)

    def __str__(self):
        if self.is_off():
            return ''
        elif self.value is True:
            return self.flag
        else:
            return '{}{}{}'.format(self.flag, self.delimiter, self.value)

    def __eq__(self, other):
        return super().__eq__(other) and other.flag == self.flag

    def _get_arg(self):
        '''Return the parameter as list.'''
        if self.is_on():
            if isinstance(self.value, bool):
                return [self.flag]
            if self.delimiter.isspace():
                return [self.flag, str(self.value)]
            else:
                return ['{}{}{}'.format(self.flag, self.delimiter, self.value)]
        else:
            return []


class Parameters(Mapping):
    '''Store the parameters of a command line executable as a `OrderedDict`.

    The parameters are stored as `OrderedDict` and this object has the same API
    with `OrderedDict`. Its value is an object of `Param`'s child class. Its
    key is either the `Param.name` or the `Param.flag`, either of which can
    be used to retrieve its value. The order of the keys in the `OrderedDict`
    is the parameter order given in __init__ and is used to order
    the parameters as in command line.

    Parameters
    ----------
    params : `Iterable`
        positional arguments of `Param` or its child classes.

    Examples
    --------
    >>> from dumpling import ArgmntParam, OptionParam, Parameters
    >>> params = [OptionParam('--force', '-f', help='force overwriting'),
    ...           ArgmntParam('input', help='input cm file')]
    >>> p = Parameters(*params)
    >>> p
    OptionParam(flag='--force', alter='-f', name='force', value=None, action=<lambda>, help='force overwriting', delimiter=' ')
    ArgmntParam(name='input', value=None, action=<lambda>, help='input cm file')
    >>> list(p.keys())
    ['force', 'input']
    >>> '--force' in p
    True
    >>> p['--force']
    OptionParam(flag='--force', alter='-f', name='force', value=None, action=<lambda>, help='force overwriting', delimiter=' ')
    >>> p['--force'] == p['-f'] == p['force']
    True
    >>> p['input']
    ArgmntParam(name='input', value=None, action=<lambda>, help='input cm file')
    >>> p['input'] = 'riboswitch.cm'
    >>> p
    OptionParam(flag='--force', alter='-f', name='force', value=None, action=<lambda>, help='force overwriting', delimiter=' ')
    ArgmntParam(name='input', value='riboswitch.cm', action=<lambda>, help='input cm file')
    >>> p.off()
    >>> p
    OptionParam(flag='--force', alter='-f', name='force', value=None, action=<lambda>, help='force overwriting', delimiter=' ')
    ArgmntParam(name='input', value=None, action=<lambda>, help='input cm file')
    >>> p.update(force=True, input='SAM.cm')
    >>> p
    OptionParam(flag='--force', alter='-f', name='force', value=True, action=<lambda>, help='force overwriting', delimiter=' ')
    ArgmntParam(name='input', value='SAM.cm', action=<lambda>, help='input cm file')
    >>> for k in p:
    ...     print(p[k])
    ...
    --force
    SAM.cm
    '''

    def __init__(self, *params):
        '''Construct an instance from a list of OptionParam or ArgmntParam.

        Parameters
        ----------
        params : list of `Param`
            a list of parameters.
        '''
        # create a copy of each param
        k_v = [(param.name, deepcopy(param)) for param in params]
        self._data = OrderedDict(k_v)
        self._name_map = {}
        for k in self._data:
            p = self._data[k]
            if isinstance(p, OptionParam):
                self._name_map[p.flag] = p.name
                self._name_map[p.alter] = p.name
            elif not isinstance(p, Param):
                raise ValueError('{} is not an instance of `Param`.'.format(p))

    def __iter__(self):
        '''Iterate over parameter in this object.

        Yields
        ------
        Param
            Child class of `Param`
        '''
        return iter(self._data)

    def __len__(self):
        '''Return the number of parameters.'''
        return len(self._data)

    def __contains__(self, key):
        '''Determine if a parameter exists.

        Parameters
        ----------
        key : str
            The flag or name of a parameter
        '''
        return key in self._data or key in self._name_map

    def __getitem__(self, key):
        '''Return the `Param` object by key.

        Parameters
        ----------
        key : str
            The name or flag of the parameter to be retrieved.
        '''
        if key in self._data:
            return self._data[key]
        elif key in self._name_map:
            return self._data[self._name_map[key]]
        else:
            raise KeyError(key)

    def __setitem__(self, k, v):
        '''Set the value of specified paramter.

        Parameters
        ----------
        k : str
            The name or flag of a parameter.
        v : arbitrary object
            The new value of the parameter.

        Raises
        ------
        ValueError
            If the key is not in this `Parameters` object.
        '''
        if k in self:
            self[k].on(v)
        else:
            msg = 'You cannot set value {!r} on unknown key {!r}'
            raise ValueError(msg.format(v, k))

    def update(self, **kwargs):
        '''Update the parameter values.

        Parameters
        ----------
        kwargs : dict
            keyword arguments. The key and value to update the parameters
            in this `Parameters` object.

        Notes
        -----
        If multiple keys of the same parameter are given, the flag key will
        be overwritten by the name key. See the examples.

        Examples
        --------
        >>> from dumpling import OptionParam, Parameters
        >>> p = Parameters(*[OptionParam('--threads', name='cpus'), OptionParam('-i')])
        >>> p
        OptionParam(flag='--threads', alter=None, name='cpus', value=None, action=<lambda>, help='', delimiter=' ')
        OptionParam(flag='-i', alter=None, name='i', value=None, action=<lambda>, help='', delimiter=' ')
        >>> p.update(cpus=2, **{'--threads': 1})
        >>> p   # '--threads' is overridden by 'cpus'
        OptionParam(flag='--threads', alter=None, name='cpus', value=2, action=<lambda>, help='', delimiter=' ')
        OptionParam(flag='-i', alter=None, name='i', value=None, action=<lambda>, help='', delimiter=' ')
        >>> p.update(**{'cpus': 3, '--threads': 1})
        >>> p
        OptionParam(flag='--threads', alter=None, name='cpus', value=3, action=<lambda>, help='', delimiter=' ')
        OptionParam(flag='-i', alter=None, name='i', value=None, action=<lambda>, help='', delimiter=' ')
        '''
        for k in sorted(kwargs):
            self[k] = kwargs[k]

    def off(self):
        '''Turn off all the parameters.'''
        for k in self._data:
            self[k].off()

    def __repr__(self):
        '''String representation of the `Parameters` object.'''
        items = []
        for k in self._data:
            items.append(repr(self._data[k]))
        return '\n'.join(items)


def dumpling_factory(name, cmd, params, version='', url=''):
    '''dumpling factory.

    Parameters
    ----------
    name : str
        The name of the class returned
    cmd : str or list of str
        The command or a list of command and its nested subcommand(s), e.g. ['git', 'clone']
    params : `Parameters`
        The parameters of the app
    version : str
        The version of the app.
    url : str
        URL of the app.

    Returns
    -------
    class
        a class object

    Examples
    --------
    >>> from dumpling import ArgmntParam, OptionParam, Parameters, dumpling_factory
    >>> from tempfile import mkdtemp
    >>> from shutil import rmtree
    >>> import os
    >>> import stat
    >>> params = [OptionParam('-f', help='force overwriting'),
    ...           ArgmntParam('input', help='input cm file')]
    >>> p = Parameters(*params)
    >>> script = r"""#!/usr/bin/env python
    ... import argparse
    ... parser = argparse.ArgumentParser(description='Test CMD.')
    ... parser.add_argument('-f', dest='f', action='store_true')
    ... parser.add_argument('input', metavar='INPUT', type=str, nargs='?')
    ... args = parser.parse_args()
    ... if __name__ == '__main__':
    ...     print('{!r}\\n{!r}'.format(args.f, args.input))
    ... """
    >>> tmpd = mkdtemp()
    >>> cmd = os.path.join(tmpd, 'test.py')
    >>> with open(cmd, 'w') as o:  # doctest: +ELLIPSIS
    ...    _ = o.write(script)
    >>> os.chmod(cmd, stat.S_IXUSR | stat.S_IRUSR)
    >>> App = dumpling_factory('test', cmd, p, '1.0.0', 'www.test.com')
    >>> app = App()   # create an instance
    >>> app  # doctest: +ELLIPSIS
    test
    ----
    CMD: ...
    CMD version: '1.0.0'
    CMD URL: 'www.test.com'
    CMD Parameter:
    OptionParam(flag='-f', alter=None, name='f', value=None, action=<lambda>, help='force overwriting', delimiter=' ')
    ArgmntParam(name='input', value=None, action=<lambda>, help='input cm file')
    >>> app.update(f=True, input='input file')
    >>> app  # doctest: +ELLIPSIS
    test
    ----
    CMD: ...
    CMD version: '1.0.0'
    CMD URL: 'www.test.com'
    CMD Parameter:
    OptionParam(flag='-f', alter=None, name='f', value=True, action=<lambda>, help='force overwriting', delimiter=' ')
    ArgmntParam(name='input', value='input file', action=<lambda>, help='input cm file')
    >>> app.command  # doctest: +ELLIPSIS
    [..., '-f', 'input file']
    >>> proc =  app()
    >>> proc.returncode
    0
    >>> print(proc.stderr)
    <BLANKLINE>
    >>> print(proc.stdout)
    True
    'input file'
    <BLANKLINE>
    >>> rmtree(tmpd)
    >>> # subcommand example
    >>> App = dumpling_factory('test', ['cmd', 'subcmd'], p, '1.0.0', 'www.test.com')
    >>> app = App()
    >>> app
    test
    ----
    CMD: cmd subcmd
    CMD version: '1.0.0'
    CMD URL: 'www.test.com'
    CMD Parameter:
    OptionParam(flag='-f', alter=None, name='f', value=None, action=<lambda>, help='force overwriting', delimiter=' ')
    ArgmntParam(name='input', value=None, action=<lambda>, help='input cm file')
    '''
    class Dumpling:
        '''Application controller.

        Parameters
        ----------
        cmd : str or list of str
            The command or a list of command and its nested subcommand(s), e.g. ['git', 'clone']
        params : `Parameters`
            The parameters of the app
        version : str
            The version of the app.
        url : str
            URL of the app.

        Attributes
        ----------
        cmd
        params
        version
        url
        command
        '''
        def __init__(self):
            if isinstance(cmd, str):
                cmd_ = [cmd]
            else:
                cmd_ = cmd
            self.cmd = cmd_
            self.params = deepcopy(params)
            self.version = version
            self.url = url

        @property
        def command(self):
            '''Command args list passed to `subprocess.Popen`.'''
            command = []
            command.extend(self.cmd)
            for k in self.params:
                p = self.params[k]
                command.extend(p._get_arg())
            return command

        def __repr__(self):
            '''Return string representation of this object.'''
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
            '''Return the command run.'''
            return ' '.join(self.command)

        def update(self, **kwargs):
            '''Update the parameters in this app controller.

            It just calls `Parameters.update` function.

            Parameters
            ----------
            kwargs : keyword arguments
                The key and value to update the parameters in this object.

            See Also
            --------
            Parameters.update
            '''
            self.params.update(**kwargs)

        def __call__(self, cwd=None, stdin=PIPE, stdout=PIPE, stderr=PIPE, check=True):
            '''Run the command.

            Parameters
            ----------
            cwd : str
                working dir
            stdin, stdout, stderr : None, str, `subprocess.DEVNULL`, and `subprocess.PIPE` (default)
                file path to store output. Use `subprocess.DEVNULL` to suppress stdout or stderr.

            Returns
            -------
            `subprocess.CompletedProcess`

            Notes
            -----
            The default value of `subprocess.PIPE` means the stdout and/or stderr
            will be collected into memory. If you expect large volume of them,
            supply file path to store the standard IO streams instead to avoid
            memory blowup.
            '''
            try:
                if isinstance(stdin, str):
                    stdin = open(stdin, 'r')
                if isinstance(stdout, str):
                    stdout = open(stdout, 'w+')
                if isinstance(stderr, str):
                    stderr = open(stderr, 'w+')
                proc = run(self.command, cwd=cwd, shell=False,
                           stdin=stdin, stdout=stdout, stderr=stderr,
                           universal_newlines=True, check=check)

            finally:
                for f in [stdin, stdout, stderr]:
                    try:
                        f.close()
                    except AttributeError:
                        pass
            return proc

    Dumpling.__name__ = name
    return Dumpling
