"""convert test events to a xunit XML file"""

import os
import sys
import time

from datetime import datetime
from socket import gethostname
from contextlib import contextmanager
from xml.sax.saxutils import quoteattr

class XunitDestination(object):
    """Manages a repository of xunit files, for writing"""

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.expected_xunit_files = []


    def write_reports(self, relative_path, suite_name, reports,
                      package_name=None):
        """write the collection of reports to the given path"""

        dest_path = self.reserve_file(relative_path)
        with open(dest_path, 'w') as outf:
            outf.write(toxml(reports, suite_name, package_name=package_name))
        return dest_path


    def reserve_file(self, relative_path):
        """reserve a XML file for the slice at <relative_path>.xml

        - the relative path will be created for you
        - not writing anything to that file is an error
        """
        if os.path.isabs(relative_path):
            raise ValueError('%s must be a relative path' % relative_path)

        dest_path = os.path.join(self.root_dir, '%s.xml' % relative_path)

        if os.path.exists(dest_path):
            raise ValueError('%r must not already exist' % dest_path)

        if dest_path in self.expected_xunit_files:
            raise ValueError('%r already reserved' % dest_path)

        dest_dir = os.path.dirname(dest_path)
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)

        self.expected_xunit_files.append(dest_path)

        return dest_path


    def check(self):
        expected = self.expected_xunit_files
        if not all(os.path.exists(path) for path in expected):
            raise Exception(
                'result files %r reserved by hook have not been produced' % (
                    set(path for path in expected if not os.path.isfile(path))
            ))


class Recorder(object):
    """Use this class to record the result of running python code as a xunit xml

    It allows you to record a series of steps into a single xunit.xml file.
    """

    def __init__(self, destination, name, package_name=None):
        self.name = name
        self.package_name = package_name
        self.destination = destination
        self.event_receiver = None


    def __enter__(self):
        self.event_receiver = EventReceiver()
        return self


    def now_seconds(self):
        return time.time()


    def step(self, step_name):
        """Start a new step. returns a context manager which allows you to
        report an error"""

        @contextmanager
        def step_context(step_name):
            if self.event_receiver.current_case is not None:
                raise Exception('cannot open a step within a step')

            self.event_receiver.begin_case(step_name, self.now_seconds(), self.name)
            try:
                yield self.event_receiver
            except:
                etype, evalue, tb = sys.exc_info()
                self.event_receiver.error('%r' % [etype, evalue, tb])
                raise
            finally:
                self.event_receiver.end_case(step_name, self.now_seconds())

        return step_context(step_name)


    def __exit__(self, *exc_info):
        results = self.event_receiver.results()
        if not results:
            already_throwing = exc_info and exc_info[0] is not None
            if not already_throwing:
                raise ValueError('your hook must at least perform one step!')

        self.destination.write_reports(
            self.name, self.name, results, package_name=self.package_name,
        )



class Report(object):
    """represents a test case report"""

    def __init__(self, name, start_ts=None, end_ts=None, src_location=None):
        self.name = name
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.src_location = src_location
        self.failures = []
        self.errors = []

    def __repr__(self):
        return '%r' % dict(
            name=self.name,
            start_ts=self.start_ts,
            end_ts=self.end_ts,
            failed=not self.errors,
            src_location=self.src_location,
        )

    def __hash__(self):
        return repr(self).__hash__()

    def __eq__(self, another):
        return repr(self) == repr(another)


class EventReceiver(object):
    """eventfull interface to collect results from test cases and produce test reports."""

    def __init__(self):
        self.cases = []
        self.current_case = None

    def end_current_case(self, ts):
        self.current_case.end_ts = ts
        self.cases.append(self.current_case)

    def begin_case(self, test_name, ts, src_location):
        if self.current_case is not None:
            self.error(ts)
            self.end_current_case(ts)

        self.current_case = Report(test_name)
        self.current_case.start_ts = ts
        self.current_case.src_location = src_location

    def end_case(self, test_name, ts):
        if self.current_case is None or self.current_case.name != test_name:
            raise Exception(
                'cannot close case %s (current: %s)' % (test_name, self.current_case)
            )
        self.end_current_case(ts)
        self.current_case = None

    def error(self, reason):
        assert self.current_case is not None
        self.current_case.errors.append(
            'error %s' % (
                reason
            )
        )

    def failure(self, reason, src_location):
        assert self.current_case is not None
        self.current_case.failures.append(
            'test failure %s at %s' % (
                reason, src_location,
            )
        )

    def results(self):
        if self.current_case is not None:
            self.error('test finished unexpectedly')
            self.end_current_case(self.current_case.start_ts)

        return self.cases


def toxml(test_reports, suite_name,
          hostname=gethostname(), package_name="tests"):
    """convert test reports into an xml file"""

    output = r'<?xml version="1.0" encoding="UTF-8"?>'
    output += '\n<testsuites>'

    test_count = len(test_reports)
    if test_count < 1:
        raise ValueError('there must be at least one test report')


    assert test_count > 0, 'expecting at least one test'

    error_count = len([r for r in test_reports if r.errors])
    failure_count = len([r for r in test_reports if r.failures])
    ts = test_reports[0].start_ts
    start_timestamp = datetime.fromtimestamp(ts).isoformat()

    total_duration = test_reports[-1].end_ts - test_reports[0].start_ts

    def quote_attribute(value):
        return quoteattr(value) if value is not None else "(null)"

    output += '<testsuite errors="%(error_count)d" tests="%(test_count)d" failures="%(failure_count)d" name=%(suite_name)s id="0" package=%(package_name)s hostname=%(hostname)s timestamp=%(start_timestamp)s time="%(total_duration)f">' % dict(
        error_count=error_count,
        failure_count=failure_count,
        test_count=test_count,
        hostname=quote_attribute(hostname),
        start_timestamp=quote_attribute(start_timestamp),
        total_duration=total_duration,
        suite_name=quote_attribute(suite_name),
        package_name=quote_attribute(package_name),
    )

    for r in test_reports:
        test_name = r.name
        test_duration = r.end_ts - r.start_ts
        class_name = r.src_location

        if r.errors or r.failures:
            output += '<testcase name=%(test_name)s classname=%(class_name)s time="%(test_duration)f">' % dict(
                test_name=quote_attribute(test_name),
                test_duration=test_duration,
                class_name=quote_attribute(class_name),
            )

            if r.failures:
                output += '<failure message=%s type="exception"/>' % quote_attribute(
                    '\n'.join(['%s' % e for e in r.failures])
                )

            else:
                output += '<error message=%s type="exception"/>' % quote_attribute(
                    '\n'.join(['%s' % e for e in r.errors])
                )

            output += '</testcase>'
        else:
            output += '<testcase name=%(test_name)s classname=%(class_name)s time="%(test_duration)f"/>' % dict(
                test_name=quote_attribute(test_name),
                test_duration=test_duration,
                class_name=quote_attribute(class_name),
            )

    output += '</testsuite>'
    output += '</testsuites>'

    return output.encode('utf-8')
