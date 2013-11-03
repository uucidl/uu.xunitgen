import os
import xml.etree.ElementTree as ET

from unittest import TestCase
from StringIO import StringIO

from lxml import etree as lxml_etree

import xunitgen.main
import xunitgen

class TestFormat(TestCase):
    def test_trivial(self):
	self.assertEquals([], xunitgen.TestEventReceiver().results())

    def test_dangling_case(self):
	receiver = xunitgen.TestEventReceiver()
	receiver.begin_case('a-test', 0, src_location='foo')

	self.assertEquals(1, len(receiver.results()[0].errors))

    def test_failure_event(self):
	receiver = xunitgen.TestEventReceiver()
	receiver.begin_case('a-test', 0, 'foo')
	receiver.failure('because', 4)
	receiver.end_case('a-test', 9)

	self.assertEquals(1, len(receiver.results()[0].failures))

    def test_tostring(self):
	test_a = xunitgen.TestReport(
	    'a-test', start_ts=0, end_ts=1000000, src_location='foo'
	)
	test_b = xunitgen.TestReport(
	    'b-test', start_ts=3000000, end_ts=5000000,
	    src_location=os.path.join('this', 'is', 'a', 'bar').replace(os.sep, '.')
	)
	test_c = xunitgen.TestReport(
	    'c-test', start_ts=3000000, end_ts=5000000,
	    src_location=os.path.join('this', 'is', 'a', 'baz').replace(os.sep, '.')
	)
	test_a.errors.append('this is an error')
	test_a.failures.append('this is a failure')
	test_b.errors.append('this is an error 2')
	test_b.errors.append('this is another error in the same test')

	test_results = [test_a, test_b, test_c]

	xunit_reference="""<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
    <testsuite errors="2" failures="1" hostname="test-hostname" id="0" name="tests" package="tests" tests="3" time="5.000000" timestamp="1970-01-01T01:00:00">
	<testcase classname="foo" name="a-test" time="1.000000">
	    <failure message="this is a failure" type="exception" />
	</testcase>
	<testcase classname="this.is.a.bar" name="b-test" time="2.000000">
	    <error message="this is an error 2\nthis is another error in the same test" type="exception" />
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

	def validate_schema(xmlstring):
	    xmlschema = None
	    with open('tests/data/jenkins-xunit.xsd') as f:
		xmlschema_doc = lxml_etree.parse(f)
		xmlschema = lxml_etree.XMLSchema(xmlschema_doc)

	    xmlstream = StringIO(xmlstring)
	    xmlschema.assertValid(lxml_etree.parse(xmlstream))

	xunit_result = xunitgen.tostring(test_results, 'test-hostname')
	validate_schema(xunit_result)
	self.assertEquals(xmlnorm(xunit_reference), xmlnorm(xunit_result))
