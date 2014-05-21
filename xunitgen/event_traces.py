"""interpret event traces as test activity

this file serves as an example for the xunitgen module

event traces are similar/compatible with those produced by uu.spdr

https://github.com/uucidl/uu.spdr
"""
from argparse import ArgumentParser

import os
import re

from socket import gethostname

from xunitgen import XunitDestination, EventReceiver, toxml


def parse_trace(line):
    main_re = r'^TT01 ([0-9]+) ([0-9]+) ([0-9]+) ("(?:[^\\"]|\\.)*") ("(?:[^\\"]|\\.)*") ("[A-Z]")(.*)$'
    match = re.match(main_re, line)
    if match:
        def get(i):
            return match.group(i)

        def unquote_str(string):
            return eval(string)

        trace = dict(
            ts=int(get(1)),
            pid=int(get(2)),
            tid=int(get(3)),
            cat=unquote_str(get(4)),
            name=unquote_str(get(5)),
            ph=unquote_str(get(6)),
            args={},
        )

        arg_str = get(7)
        if arg_str:
            for match in re.finditer(r' ("(?:[^\\"]|\\.)*") ((?:"(?:[^\\"]|\\.)*")|(?:[0-9]+\.[0-9]*)|(?:[0-9]+))', arg_str):
                name = unquote_str(get(1))
                value_str = get(2)
                if re.match(r'^"(?:[^\\"]|\\.)*"$', value_str):
                    value = unquote_str(value_str)
                elif re.match(r'^[0-9]+\.[0-9]*$', value_str):
                    value = float(value_str)
                elif re.match(r'^[0-9]+$', value_str):
                    value = int(value_str)

                trace['args'][name] = value

            if not trace['args']:
                raise Exception('Could not parse args %r' % arg_str)

        return trace

    raise Exception('Could not parse %r' % line)


def gather_test_results(traces):
    MICROS_TO_S = 1000000.0
    receiver = EventReceiver()

    for trace in traces:
        ts_seconds = trace['ts'] / MICROS_TO_S
        if trace['cat'] == 'test':
            if trace['ph'] == 'E' and receiver.current_case.name == trace['name']:
                receiver.end_case(trace['name'], ts_seconds)
            elif trace['ph'] == 'B' and receiver.current_case is None:
                receiver.begin_case(
                    trace['name'], ts_seconds, os.path.splitext(
                        trace['args']['filename'])[0].replace(os.sep, '.')
                )
            elif trace['ph'] == 'I' and trace['name'] == 'failure':
                receiver.failure(trace['args'][
                                 'reason'], trace['args']['lineno'])

    return receiver.results()


def main():
    parser = ArgumentParser()
    parser.add_argument("dst_xunit_file")
    parser.add_argument("src_trace_log")

    args = parser.parse_args()

    destination = XunitDestination(os.path.dirname(os.path.abspath(args.dst_xunit_file)))
    xml_filepath = os.path.splitext(os.path.basename(args.dst_xunit_file))[0]
    with open(args.src_trace_log) as file:
        def parse_line(line_i, line):
            try:
                return parse_trace(line)
            except Exception as e:
                raise Exception('%s:%d: error: %r' % (
                    args.src_trace_log, i, e))

        test_results = gather_test_results(
            [parse_line(i, line) for i, line in enumerate(file.readlines())]
        )

    destination.write_reports(xml_filepath, 'testsuite', test_results)


if __name__ == "__main__":
    main()
