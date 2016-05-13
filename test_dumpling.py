from unittest import TestCase, main
from tempfile import mkdtemp
from collections import namedtuple
from shutil import rmtree
from os.path import join, realpath
from subprocess import DEVNULL, CalledProcessError
import os
import stat

from dumpling import (
    ArgmntParam, OptionParam, Parameters, dumpling_factory,
    check_choice, check_range)


class CheckTests(TestCase):
    def test_check_choice(self):
        checker = check_choice(range(3))
        val = 1
        self.assertEqual(val, checker(val))
        val = 5
        with self.assertRaises(ValueError):
            checker(val)

    def test_check_range(self):
        checker = check_range(0, 9)
        val = 3
        self.assertEqual(val, checker(val))
        val = 11
        with self.assertRaises(ValueError):
            checker(val)


class Tests(TestCase):
    def setUp(self):
        self.tests = [
            OptionParam('--db', value='file path'),
            OptionParam('-e', value=0.1, action=check_range(0, 1000)),
            OptionParam('-1', name='r1', value=False, help='Left-end read'),
            ArgmntParam('out', 'output.txt')]
        self.params = Parameters(*self.tests)


class ArgmntParamTests(Tests):
    def test_repr(self):
        exp = "ArgmntParam(name='out', value='output.txt', action=<lambda>, help='')"
        self.assertEqual(repr(self.tests[-1]), exp)

    def test_get_arg(self):
        p = self.tests[-1]
        exp = [p.value]
        self.assertEqual(p._get_arg(), exp)
        p.off()
        self.assertEqual(p._get_arg(), [])


class OptionParamTests(Tests):
    def test_init(self):
        attrs = ['flag', 'name', 'value', 'help']
        Exp = namedtuple('Exp', attrs)
        exps = [Exp('--db', 'db', 'file path', ''),
                Exp('-e', 'e', 0.1, ''),
                Exp('-1', 'r1', False, 'Left-end read')]
        for test, exp in zip(self.tests, exps):
            for attr in attrs:
                self.assertEqual(getattr(test, attr), getattr(exp, attr))

    def test_init_raise(self):
        tests = [('a', check_choice(['b', 'c'])),
                 (9, check_choice(range(8))),
                 (1, check_range(2, 6))]
        for v, f in tests:
            with self.assertRaises(ValueError):
                OptionParam('-i', value=v, action=f)

    def test_is_on(self):
        exps = [True, True, False]
        for test, exp in zip(self.tests, exps):
            self.assertEqual(test.is_on(), exp)

    def test_value_set(self):
        param = self.tests[0]
        param.value = 'input file'
        self.assertEqual(param.value, 'input file')
        param.on(None)
        self.assertEqual(param.value, None)

    def test_value_set_raise(self):
        param = self.tests[1]
        with self.assertRaises(ValueError):
            param.value = -1
        with self.assertRaises(ValueError):
            param.on(-2)

    def test_repr(self):
        exp = ("OptionParam(flag='-e', name='e', value=0.1, "
               "action=<lambda>, help='', delimiter=' ')")
        self.assertTrue(exp, repr(self.tests[1]))

    def test_str(self):
        exps = ["--db file path", '-e 0.1']
        for test, exp in zip(self.tests, exps):
            self.assertEqual(str(test), exp)

    def test_eq(self):
        a = OptionParam(flag='-i', name='input')
        b = OptionParam(flag='-i', name='i')
        self.assertEqual(a, b)
        a.on(2)
        b.on(1)
        self.assertNotEqual(a, b)
        a = OptionParam(flag='-o', name='i')
        b = OptionParam(flag='-i', name='i')
        self.assertNotEqual(a, b)

    def test_get_args(self):
        p = self.tests[1]
        exp = ['-e', '0.1']
        self.assertEqual(p._get_arg(), exp)
        p.off()
        self.assertEqual(p._get_arg(), [])


class ParametersTests(Tests):
    def test_len(self):
        params = Parameters()
        self.assertEqual(len(params), 0)
        self.assertEqual(len(self.tests), len(self.params))

    def test_getitem(self):
        for p in self.tests:
            self.assertEqual(p, self.params[p.name])
            if isinstance(p, OptionParam):
                self.assertEqual(p, self.params[p.name])

    def test_getitem_raise(self):
        with self.assertRaises(KeyError):
            self.params['xxx']

    def test_setitem(self):
        vs = ['spam', 1, False]
        for p, v in zip(self.tests, vs):
            name = p.name
            old_v = p.value
            self.params[name] = v
            self.assertEqual(self.params[name], p.on(v))
            name = p.name
            self.params[name] = old_v
            self.assertEqual(self.params[name], p.on(old_v))

    def test_setitem_raise(self):
        with self.assertRaises(ValueError):
            self.params['xxx'] = 3

    def test_contains(self):
        for k in self.params:
            self.assertTrue(k in self.params)

        for name in self.params._name_map:
            self.assertTrue(name in self.params)

        self.assertFalse('xxx' in self.params)

    def test_off(self):
        self.params.off()
        for k in self.params:
            self.assertTrue(self.params[k].value is None)

    def test_update(self):
        kv = {'db': 'db.txt',
              'e': 3}
        self.params.update(**kv)
        for k in kv:
            self.assertEqual(self.params[k].value, kv[k])
        # check the not updated param is still the same
        self.assertEqual(self.params['r1'], self.tests[2])


class DumplingTests(Tests):
    def setUp(self):
        super().setUp()
        script_name = 'test.py'
        self.tmpd = mkdtemp()
        self.cmd = join(self.tmpd, script_name)
        with open(self.cmd, 'w') as o:
            o.write(script)
        os.chmod(self.cmd, stat.S_IXUSR | stat.S_IRUSR)
        self.version = '1.0.9'
        self.url = 'www.test.com'
        self.TestApp = dumpling_factory(script_name, self.cmd, self.params, self.version, self.url)

    def test_init(self):
        app = self.TestApp()
        self.assertEqual(app.version, self.version)
        self.assertEqual(app.url, self.url)
        self.assertEqual(app.params, self.params)
        self.assertEqual(app.cmd, [self.cmd])

    def test_repr(self):
        exp = ('''test.py
-------
CMD: {}
CMD version: '1.0.9'
CMD URL: 'www.test.com'
CMD Parameter:
OptionParam(flag='--db', alter=None, name='db', value='file path', action=<lambda>, help='', delimiter=' ')
OptionParam(flag='-e', alter=None, name='e', value=0.1, action=func, help='', delimiter=' ')
OptionParam(flag='-1', alter=None, name='r1', value=False, action=<lambda>, help='Left-end read', delimiter=' ')
ArgmntParam(name='out', value='output.txt', action=<lambda>, help='')''').format(self.cmd)
        self.assertEqual(repr(self.TestApp()), exp)

    def test_call_fail(self):
        with self.assertRaises(CalledProcessError):
            app = self.TestApp()
            app()

    def test_call_succeed(self):
        app = self.TestApp()
        app.update(e=3, r1='R1.fq', out='output.txt')
        p = app()
        out = 'directory: {}\nfile path\n3.0\nR1.fq\noutput.txt\n'.format(os.getcwd())
        err = ''
        self.assertEqual(p.stdout, out)
        self.assertEqual(p.stderr, err)
        self.assertEqual(p.returncode, 0)

    def test_call_no_stdout_stderr(self):
        app = self.TestApp()
        app.update(e=3, r1='R1.fq', out='output.txt')
        p = app(stdout=DEVNULL, stderr=DEVNULL)
        self.assertEqual(p.stdout, None)
        self.assertEqual(p.stderr, None)
        self.assertEqual(p.returncode, 0)

    def test_call_cwd_stdout_stderr(self):
        o = join(self.tmpd, 'stdout')
        e = join(self.tmpd, 'stderr')
        with self.assertRaises(CalledProcessError):
            app = self.TestApp()
            app(stdout=o, stderr=e)

        stdout = 'directory: {}\n'
        stderr = '''usage: test.py [-h] --db DB -e E -1 R1 [OUT]
test.py: error: the following arguments are required: -1
'''
        with open(o) as out:
            self.assertEqual(out.read(), stdout.format(os.getcwd()))
        with open(e) as err:
            self.assertEqual(err.read(), stderr)

        # test changing working dir and PIPE for stdout/stderr
        try:
            app(cwd=self.tmpd)
        except CalledProcessError as e:
            # realpath is necessary because of /tmp/ is a symbolic link to /private/tmp
            self.assertEqual(e.stdout, stdout.format(realpath(self.tmpd)))
            self.assertEqual(e.stderr, stderr)

    def tearDown(self):
        rmtree(self.tmpd)


script = r'''#!/usr/bin/env python
import argparse
from os import getcwd

def interface():
    parser = argparse.ArgumentParser(description='Test CMD for dumpling.')
    parser.add_argument('--db', dest='db', type=str, default='default.db', required=True)
    parser.add_argument('-e', dest='e', type=float, default=1, required=True)
    parser.add_argument('-1', dest='r1', required=True)
    parser.add_argument('out', metavar='OUT', type=str, nargs='?')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    print('directory: {}'.format(getcwd()))
    args = interface()
    print('\n'.join([args.db, str(args.e), args.r1, args.out]))
'''


if __name__ == '__main__':
    main()
