Travis-CI: <https://travis-ci.org/uucidl/uu.xunitgen.svg?branch=master>

Abstract
========

`xunitgen` is a python module for the simple production of `xunit` or
`junit` XML files for use in continuous integration. Such as with
`Jenkins`.

It converts a stream of timed (start/finish/error) events and convert
them into a report.

It brings / need no dependencies besides an installation of `Python 2`
or `Python 3`.

Using
=====

Once you have added the directory surrounding `xunitgen` into your
`PYTHONPATH`, you can create simple test steps by using the
xunitgen.Recorder:

``` {.python}
import xunitgen

destination = xunitgen.XunitDestination('.')

with xunitgen.Recorder(destination, 'my-test-suite') as recorder:
    with recorder.step('a-success') as step:
        pass

    with recorder.step('a-failing-test') as step:
        step.error('this step has failed')

    with recorder.step('another-failing-test'):
        raise Exception('I have failed too!')
```

Which will produce a file named my-test-suite.xml under the current
directory

Lower level, event API
----------------------

You can also use a lower level API (EventReceiver) if you need finer
control:

``` {.python}
import xunitgen

receiver = xunitgen.EventReceiver()
receiver.begin_case('a-test', 0, 'foo')
receiver.failure('because', 'ExceptionFoo')
receiver.end_case('a-test', 9)

print xunitgen.tostring(receiver.results())
```

Example (event\_trace module)
-----------------------------

The xunitgen.event\_trace module shows an example of using the lower
level API to convert a tracing format to xUnit files. This can be used
for instance by C programs/tests to produce test traces without having
to implement the xUnit format.

*xunitgen/event\_traces.py*

Contributing
============

If you want to make code contributions to `xunitgen` here are the steps
to follow to get a working development environment:

Create a virtual environment and activate it

``` {.example}
$ virtualenv venv
$ . venv/bin/activate
```

Install development dependencies

``` {.example}
$ pip install -r dev_requirements.txt
```

With the virtual environment active, test your changes before
submitting:

``` {.example}
$ nosetests -s tests
```

Additional Contributors
=======================

-   Diez Roggisch \<dir@ableton.com\>
