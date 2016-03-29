from unittest import TestCase, main
from shlex import quote
from collections import namedtuple

from dumpling.param import (
    OptionParam, check_choice, check_range,
    Parameters)


class Tests(TestCase):
    def setUp(self):
        self.tests = [
            OptionParam('-i'),
            OptionParam('--output', value='file path', alias='o', formatter=quote),
            OptionParam('-e', value=0.1, formatter=check_range(0, 1000)),
            OptionParam('-1', value=True, help='Left-end read')]


class OptionParamTests(Tests):
    def test_init(self):
        attrs = ['name', 'alias', 'value', 'help']
        Exp = namedtuple('Exp', attrs)
        exps = [Exp('-i', 'i', None, ''),
                Exp('--output', 'o', "'file path'", ''),
                Exp('-e', 'e', 0.1, ''),
                Exp('-1', '_1', True, 'Left-end read')]
        for test, exp in zip(self.tests, exps):
            for attr in attrs:
                self.assertEqual(getattr(test, attr), getattr(exp, attr))

    def test_init_raise(self):
        tests = [('a', check_choice(['b', 'c'])),
                 (9, check_choice(range(8))),
                 (1, check_range(2, 6))]
        for v, f in tests:
            with self.assertRaises(ValueError):
                OptionParam('-i', value=v, formatter=f)

    def test_is_on(self):
        exps = [False, True, True, True]
        for test, exp in zip(self.tests, exps):
            self.assertEqual(test.is_on(), exp)

    def test_value_set(self):
        param = self.tests[1]
        param.value = 'input file'
        self.assertEqual(param.value, "'input file'")
        param.on(None)
        self.assertEqual(param.value, None)

    def test_value_set_raise(self):
        param = self.tests[2]
        with self.assertRaises(ValueError):
            param.value = -1
        with self.assertRaises(ValueError):
            param.on(-2)

    def test_repr(self):
        exp = 'OptionParam(name="-i", alias="i", value=None, formatter=<lambda>, help="", delimiter=" ")'
        self.assertEqual(repr(self.tests[0]), exp)

    def test_str(self):
        exps = ['', "--output 'file path'", '-e 0.1', '-1']
        for test, exp in zip(self.tests, exps):
            self.assertEqual(str(test), exp)

    def test_eq(self):
        a = OptionParam(name='-i', alias='input')
        b = OptionParam(name='-i', alias='i')
        self.assertEqual(a, b)
        a.on(2)
        b.on(1)
        self.assertNotEqual(a, b)
        a = OptionParam(name='-o', alias='i')
        b = OptionParam(name='-i', alias='i')
        self.assertNotEqual(a, b)


class ParametersTests(Tests):
    def setUp(self):
        super().setUp()
        self.params = Parameters.from_params(self.tests)

    def test_len(self):
        params = Parameters([])
        self.assertEqual(len(params), 0)
        self.assertEqual(len(self.tests), len(self.params))

    def test_getitem(self):
        for p in self.tests:
            self.assertEqual(p, self.params[p.name])
            self.assertEqual(p, self.params[p.alias])

    def test_getitem_raise(self):
        with self.assertRaises(KeyError):
            self.params['xxx']

    def test_setitem(self):
        vs = ['foo', 'spam', 1, False]
        for p, v in zip(self.tests, vs):
            name = p.name
            old_v = p.value
            self.params[name] = v
            self.assertEqual(self.params[name], p.on(v))
            name = p.alias
            self.params[name] = old_v
            self.assertEqual(self.params[name], p.on(old_v))

    def test_setitem_raise(self):
        with self.assertRaises(ValueError):
            self.params['xxx'] = 3


if __name__ == '__main__':
    main()
