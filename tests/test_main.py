import os
import xml.etree.ElementTree as ET

from unittest import TestCase
from StringIO import StringIO

from lxml import etree as lxml_etree

from xunitgen import (
    EventReceiver,
    Recorder,
    Report,
    toxml,
)


def validate_schema(xmlstring):
    xmlschema = None
    with open(os.path.join(os.path.dirname(__file__), 'data/jenkins-xunit.xsd')) as f:
        xmlschema_doc = lxml_etree.parse(f)
        xmlschema = lxml_etree.XMLSchema(xmlschema_doc)

    xmlstream = StringIO(xmlstring)
    doc = lxml_etree.parse(xmlstream)
    xmlschema.assertValid(doc)


class TestFormat(TestCase):
    def test_trivial(self):
        self.assertEquals([], EventReceiver().results())

    def test_dangling_case(self):
        receiver = EventReceiver()
        receiver.begin_case('a-test', 0, src_location='foo')

        self.assertEquals(1, len(receiver.results()[0].errors))

    def test_failure_event(self):
        receiver = EventReceiver()
        receiver.begin_case('a-test', 0, 'foo')
        receiver.failure('because', 4)
        receiver.end_case('a-test', 9)

        self.assertEquals(1, len(receiver.results()[0].failures))


    def test_recorder_is_a_context(self):
        self.assertRaises(Exception, Recorder(None, 'fake-name').step('step without recorder context'))


    def test_recorder_no_two_step_at_a_time(self):
        class MockDestination(object):
            def __init__(self):
                self.reports = {}

            def write_reports(self, relative_path, suite_name, test_reports):
                self.reports[relative_path] = suite_name, test_reports

        def inner_step(rec):
            with rec.step('forbidden-inner-step'):
                pass

        destination = MockDestination()
        with Recorder(destination, 'fake-name') as rec:
            with rec.step('normal-step'):
                self.assertRaises(Exception, inner_step, rec)

        name, reports = destination.reports['fake-name']
        self.assertEquals('fake-name', name)
        self.assertEquals(1, len(reports))


    def test_recorder_step(self):
        class MockDestination(object):
            def __init__(self):
                self.reports = {}

            def write_reports(self, relative_path, suite_name, test_reports):
                self.reports[relative_path] = suite_name, test_reports

        destination = MockDestination()

        with Recorder(destination, 'fake-name') as recorder:
            with recorder.step('successful-step'):
                pass

        name, reports = destination.reports['fake-name']
        self.assertEquals('fake-name', name)
        self.assertEquals(1, len(reports))
        self.assertEquals('successful-step', reports[0].name)
        assert not reports[0].failures
        assert not reports[0].errors


    def test_recorder_step_with_error(self):
        class MockDestination(object):
            def __init__(self):
                self.reports = {}

            def write_reports(self, relative_path, suite_name, reports):
                self.reports[relative_path] = suite_name, reports

        destination = MockDestination()

        try:
            with Recorder(destination, 'fake-name') as rec:
                with rec.step('failing-step'):
                    raise Exception
            assert False
        except Exception:
            pass

        name, reports = destination.reports['fake-name']
        self.assertEquals('fake-name', name)
        self.assertEquals(1, len(reports))
        self.assertEquals('failing-step', reports[0].name)
        self.assertEquals(1, len(reports[0].errors))
        assert not reports[0].failures


    def test_toxml_without_report (self):
        self.assertRaises(ValueError, toxml, [], None)


    def test_toxml(self):
        test_a = Report(
            'a-test', start_ts=0, end_ts=1, src_location='foo'
        )
        test_b = Report(
            'b-test', start_ts=3, end_ts=5,
            src_location=os.path.join(
                'this', 'is', 'a', 'bar').replace(os.sep, '.')
        )
        test_c = Report(
            'c-test', start_ts=3, end_ts=5,
            src_location=os.path.join(
                'this', 'is', 'a', 'baz').replace(os.sep, '.')
        )

        test_a.errors.append('this is an error')
        test_a.failures.append('this is a failure')
        test_b.errors.append('this is an error 2')
        test_b.errors.append('this is another error in the same test')

        test_reports = [test_a, test_b, test_c]

        xunit_reference = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
    <testsuite errors="2" failures="1" hostname="test-hostname" id="0" name="tests" package="tests" tests="3" time="5.000000" timestamp="1970-01-01T01:00:00">
        <testcase classname="foo" name="a-test" time="1.000000">
            <failure message="this is a failure" type="exception" />
        </testcase>
        <testcase classname="this.is.a.bar" name="b-test" time="2.000000">
            <error message="this is an error 2&#10;this is another error in the same test" type="exception" />
        </testcase>
        <testcase classname="this.is.a.baz" name="c-test" time="2.000000"/>
    </testsuite>
</testsuites>
"""

        def xmlnorm(xmlstring):
            et = ET.fromstring(xmlstring)
            for e in [et] + et.findall('.//'):
                if e.tail is not None:
                    e.tail = e.tail.strip(' \t\n\r')
                if e.text is not None:
                    e.text = e.text.strip(' \t\n\r')

            return ET.tostring(et)

        xunit_result = toxml(test_reports, 'tests', 'test-hostname')
        print xunit_result
        self.assertEquals(xmlnorm(xunit_reference), xmlnorm(xunit_result))
        validate_schema(xunit_result)


    def test_toxml_must_escape_its_content(self):
        test_a = Report(
            '<a-test>', start_ts=0, end_ts=1, src_location='<"world">'
        )
        test_a.errors.append('<a solid piece of "content">')
        test_b = Report(
            '<b-test>', start_ts=0, end_ts=1, src_location='<"world">'
        )
        test_b.errors.append('<a "solid" piece of content>')
        xunit_result = toxml([test_a, test_b], 'escape-tests', 'test-hostname')
        validate_schema(xunit_result)


    def test_toxml_must_accept_unicode(self):
        test_a = Report(
            '<a-test>', start_ts=0, end_ts=1, src_location=u'\u4e16\u754c'
        )
        xunit_result = toxml([test_a], 'unicode-tests', 'test-hostname')
        validate_schema(xunit_result)
