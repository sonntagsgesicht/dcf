# -*- coding: utf-8 -*-

# regtest
# -------
# regression test enhancement for the Python unittest framework.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Wednesday, 18 September 2019
# Website:  https://github.com/sonntagsgesicht/regtest
# License:  Apache License 2.0 (see LICENSE file)


from inspect import stack
from json import load, dump
from logging import getLogger, NullHandler
from os.path import exists, sep, join
from os import makedirs
from unittest import TestCase
from gzip import open

EXT = '.json.zip'

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class _ignore_(object):
    pass


class MissingAssertValueError(KeyError):
    pass


class LeftoverAssertValueError(KeyError):
    pass


class RegressionTestCase(TestCase):

    folder = join('test', 'data')
    silent = False

    @property
    def _folder(self):
        return self.folder + sep + self.__class__.__name__

    @property
    def filenames(self):
        return tuple(self.filename(m) for m in self.testmethodnames)

    @property
    def testmethodnames(self):
        return tuple(m for m in dir(self) if m.startswith('test'))

    @property
    def rerun(self):
        return self._get_testmethod() in self._last_results

    def __init__(self, *args, **kwargs):
        super(RegressionTestCase, self).__init__(*args, **kwargs)
        self._last_results = dict()
        self._new_results = dict()

    def filename(self, test_method):
        return self._folder + sep + str(test_method) + EXT

    def setUp(self):
        logger.info('')
        self.readResults()

    def tearDown(self):
        self.validateResults()
        self.writeResults()

    def validateResults(self):
        # validate all values have been used
        for key in self._new_results:
            leftover = self._last_results.get(key)
            if leftover:
                args = self.__class__.__name__, key, repr(leftover)
                msg = 'requested less values than available ' \
                      'for %s.%s: %s' % args
                if self.__class__.silent:
                    logger.warning(msg)
                else:
                    raise LeftoverAssertValueError(msg)

    def readResults(self):
        folder = self.folder + sep
        logger.info('read from %s' % folder)
        for test_method in self.testmethodnames:
            file_name = self.filename(test_method)
            if exists(file_name):
                logger.info('  %s' % file_name.replace(folder, ''))
                with open(file_name, 'rt') as file:
                    self._last_results[test_method] = load(file)

    def writeResults(self):
        makedirs(self._folder, exist_ok=True)
        folder = self.folder + sep
        logger.info('write to %s' % folder)
        for test_method, data in list(self._new_results.items()):
            if test_method not in self._last_results:
                file_name = self.filename(test_method)
                logger.info('  %s' % file_name.replace(folder, ''))
                with open(file_name, 'wt') as file:
                    dump(data, file, indent=2)

    def assertAlmostRegressiveEqual(
            self, new, places=7, msg=None, delta=None, key=()):
        self._write_new(new, key)
        last = self._read_last(key)
        if last is _ignore_:
            return
        self._log_assert_call(last, new, places, msg, delta)
        try:
            return super(RegressionTestCase, self).assertAlmostEqual(
                last, new, places, msg, delta)
        except AssertionError as e:
            if self.silent:
                logger.warning(str(e))
            else:
                raise e

    def assertRegressiveEqual(self, new, msg=None, key=()):
        self._write_new(new, key)
        last = self._read_last(key)
        if last is _ignore_:
            return
        self._log_assert_call(last, new, msg)
        try:
            return super(RegressionTestCase, self).assertEqual(last, new, msg)
        except AssertionError as e:
            if self.silent:
                logger.warning(str(e))
            else:
                raise e

    def _log_assert_call(self, *args, **kwargs):
        test_method = self.__class__.__name__ + '.' + \
                      RegressionTestCase._gather_method('test')
        assert_method = RegressionTestCase._gather_method('assert')
        pp = (lambda k, v: '%s: %s' % (str(k), repr(v)))
        kwargs = tuple(map(pp, kwargs))
        args = ', '.join(map(repr, args + kwargs))
        logger.debug('%-20s %s(%s)' % (test_method, assert_method, args))

    @staticmethod
    def _gather_method(name):
        m = None
        for line in reversed(stack()):
            if line[3].lower().startswith(name.lower()):
                m = line[3]
        if m is None:
            raise KeyError
        return m

    def _get_testmethod(self):
        return self._gather_method('test')

    def _read_last(self, key=()):
        testmethod = self._get_testmethod()
        key = key if key else testmethod
        if key in self._last_results:
            if self._last_results[key]:
                return self._last_results[key].pop(0)
            msg = 'requested more values than available for %s.%s.%s' % \
                  (self.__class__.__name__, testmethod, key)
            if self.__class__.silent:
                logger.warning(msg)
            else:
                raise MissingAssertValueError(msg)
        return _ignore_

    def _write_new(self, new, key=()):
        testmethod = self._get_testmethod()
        key = key if key else testmethod
        if key not in self._new_results:
            self._new_results[key] = list()
        self._new_results[key].append(new)
