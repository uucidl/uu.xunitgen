import os
import shutil

from unittest import TestCase
from tempfile import mkdtemp

from xunitgen import (
    XunitDestination, Report
)


class TestXunitDestination(TestCase):
    def setUp(self):
        self.root_dir = mkdtemp()
        self.destination = XunitDestination(self.root_dir)


    def tearDown(self):
        shutil.rmtree(self.root_dir)


    def test_reserve_file(self):
        path = self.destination.reserve_file('a-file')
        self.assertEquals(os.path.join(self.root_dir, 'a-file.xml'), path)
        assert not os.path.exists(path)


    def test_reserve_file_with_subdir(self):
        self.destination.reserve_file(os.path.join('a', 'b', 'c'))
        assert os.path.isdir(os.path.join(self.root_dir, 'a', 'b'))
        assert not os.path.exists(os.path.join(self.root_dir, 'a', 'b', 'c.xml'))


    def test_reserve_file_is_xml(self):
        path = self.destination.reserve_file(os.path.join('a', 'b', 'c'))
        assert path.endswith('xml')


    def test_a_reserved_file_duely_filled(self):
        path = self.destination.reserve_file('a-file')
        with open(path, 'w') as outf:
            outf.write('garbage')

        self.destination.check()


    def test_cannot_reserve_twice_the_same(self):
        self.destination.reserve_file('a-file')
        self.assertRaises(ValueError, self.destination.reserve_file, 'a-file')


    def test_cannot_reserve_existing(self):
        with open(os.path.join(self.root_dir, 'hello.xml'), 'w') as outf:
            outf.write('garbage')
        self.assertRaises(ValueError, self.destination.reserve_file, 'hello')


    def test_can_reserve_many(self):
        self.destination.reserve_file('a-file')
        self.destination.reserve_file('b-file')


    def test_write_reports(self):
        ts_origin = 1401278400
        path = self.destination.write_reports('hello', 'a-suite', [Report('a-case', start_ts=ts_origin+0, end_ts=ts_origin+0)])
        assert os.path.isfile(path)
        self.destination.check()
        self.assertRaises(ValueError, self.destination.reserve_file, 'hello')
