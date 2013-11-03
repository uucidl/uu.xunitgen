from unittest import TestCase

import xunitgen.event_traces

class TestParser(TestCase):
    def test_parse_trace(self):
	line = 'TT01 44957283965 33366 140735319652704 "test" "test_harmonic" "B"'
	trace = dict(
	    ts=44957283965,
	    pid=33366,
	    tid=140735319652704,
	    cat='test',
	    name='test_harmonic',
	    ph='B',
	    args={},
	)
	self.assertEquals(trace, xunitgen.event_traces.parse_trace(line))

    def test_parse_trace_with_parms(self):
	line = r'TT01 44957283965 33366 140735319652704 "test" "test_harmonic" "B" "str" "a\tstring\n" "int" 1 "float" 2.453'
	trace = dict(
	    ts=44957283965,
	    pid=33366,
	    tid=140735319652704,
	    cat='test',
	    name='test_harmonic',
	    ph='B',
	    args=dict(
		str='a\tstring\n',
		int=1,
		float=2.453,
	    )
	)
	self.assertEquals(trace, xunitgen.event_traces.parse_trace(line))

    def test_parse_trace_with_escapes(self):
	line = r'TT01 44957283965 33366 140735319652704 "test\ndeux" "test_harmonic" "B"'
	trace = dict(
	    ts=44957283965,
	    pid=33366,
	    tid=140735319652704,
	    cat='test\ndeux',
	    name='test_harmonic',
	    ph='B',
	    args={},
	)
	self.assertEquals(trace, xunitgen.event_traces.parse_trace(line))

    def test_gather_test_results_trivial(self):
	self.assertEquals([], xunitgen.event_traces.gather_test_results([]))

    def test_gather_test_results(self):
	traces = [
	    dict(ts=0, cat='test', name='a-test', ph='B', args=dict(
		filename='foo')
	     ),
	    dict(ts=3, cat='bleh', name='please-ignore'),
	    dict(ts=6, cat='test', name='another-test', ph='B'),
	    dict(ts=8, cat='test', name='another-test', ph='E'),
	    dict(ts=9, cat='test', name='a-test', ph='E'),
	]

	self.assertEquals([
	    xunitgen.TestReport('a-test', start_ts=0, end_ts=9, src_location='foo'),
	], xunitgen.event_traces.gather_test_results(traces))
