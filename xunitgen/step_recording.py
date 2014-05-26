import sys
import time

from contextlib import contextmanager

from .main import EventReceiver

class Recorder(object):
    """Use this class to record the result of running python code as a xunit xml

    It allows you to record a series of steps into a single xunit.xml file.

    """

    def __init__(self, xunit_destination, name, package_name=None):
        self.name = name
        self.package_name = package_name
        self.destination = xunit_destination
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
