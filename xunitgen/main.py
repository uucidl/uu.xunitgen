"""convert test events to a xunit XML file"""

from datetime import datetime
from socket import gethostname
from xml.sax.saxutils import quoteattr

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

    output = u'<?xml version="1.0" encoding="UTF-8"?>'
    output += u'\n<testsuites>'

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

    output += u'<testsuite errors="%(error_count)d" tests="%(test_count)d" failures="%(failure_count)d" name=%(suite_name)s id="0" package=%(package_name)s hostname=%(hostname)s timestamp=%(start_timestamp)s time="%(total_duration)f">' % dict(
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
            output += u'<testcase name=%(test_name)s classname=%(class_name)s time="%(test_duration)f">' % dict(
                test_name=quote_attribute(test_name),
                test_duration=test_duration,
                class_name=quote_attribute(class_name),
            )

            if r.failures:
                output += u'<failure message=%s type="exception"/>' % quote_attribute(
                    '\n'.join(['%s' % e for e in r.failures])
                )

            else:
                output += u'<error message=%s type="exception"/>' % quote_attribute(
                    '\n'.join(['%s' % e for e in r.errors])
                )

            output += u'</testcase>'
        else:
            output += u'<testcase name=%(test_name)s classname=%(class_name)s time="%(test_duration)f"/>' % dict(
                test_name=quote_attribute(test_name),
                test_duration=test_duration,
                class_name=quote_attribute(class_name),
            )

    output += u'</testsuite>'
    output += u'</testsuites>'

    return output.encode('utf-8')
