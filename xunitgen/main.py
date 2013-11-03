"""convert test events to a xunit XML file"""

import os

from datetime import datetime
from socket import gethostname

class TestReport(object):
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

class TestEventReceiver(object):
    def __init__(self):
	self.cases = []
	self.current_case = None

    def end_current_case(self, ts_microseconds):
	self.current_case.end_ts = ts_microseconds
	self.cases.append(self.current_case)

    def begin_case(self, test_name, ts_microseconds, src_location):
	if self.current_case is not None:
	    self.error(ts_microseconds)
	    self.end_current_case(ts_microseconds)

	self.current_case = TestReport(test_name)
	self.current_case.start_ts = ts_microseconds
	self.current_case.src_location = src_location

    def end_case(self, test_name, ts_microseconds):
	assert self.current_case is not None and self.current_case.name == test_name
	self.end_current_case(ts_microseconds)
	self.current_case = None

    def error(self, reason):
	assert self.current_case is not None
	self.current_case.errors.append(
	    'error %r' % (
		reason
	    )
	)

    def failure(self, reason, src_location):
	assert self.current_case is not None
	self.current_case.failures.append(
	    'test failure %r at %s' % (
		reason, src_location,
	    )
	)

    def results(self):
	if self.current_case is not None:
	    self.error('test finished unexpectedly')
	    self.end_current_case(self.current_case.start_ts)

	return self.cases

def tostring(test_results, hostname=gethostname()):
    def micros_to_s(micros):
	micros_per_s = 1000000.0
	return micros / micros_per_s

    output = r'<?xml version="1.0" encoding="UTF-8"?>'
    output += '\n<testsuites>'

    test_count = len(test_results)
    assert test_count > 0, 'expecting at least one test'

    error_count = len([r for r in test_results if r.errors])
    failure_count = 0
    ts_micros = test_results[0].start_ts
    start_timestamp = datetime.fromtimestamp(micros_to_s(ts_micros)).isoformat()

    total_duration = micros_to_s(
	test_results[-1].end_ts - test_results[0].start_ts
    )

    output += '<testsuite errors="%(error_count)d" tests="%(test_count)d" failures="%(failure_count)d" name="tests" id="0" package="tests" hostname="%(hostname)s" timestamp="%(start_timestamp)s" time="%(total_duration)f">' % locals()

    for r in test_results:
	test_name = r.name
	test_duration = micros_to_s(r.end_ts - r.start_ts)
	class_name = r.src_location

	if r.errors:
	    output += '<testcase name="%(test_name)s" classname="%(class_name)s" time="%(test_duration)f">' % locals()
	    for e in r.errors:
		output += '<error message="%s" type="exception"/>' % e

	    output += '</testcase>'
	else:
	    output += '<testcase name="%(test_name)s" classname="%(class_name)s" time="%(test_duration)f"/>' % locals()

    output += '</testsuite>'
    output += '</testsuites>'

    return output
