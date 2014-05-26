import os

from .main import toxml

class XunitDestination(object):
    """Manages a repository of xunit files, for writing test reports"""

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.expected_xunit_files = []


    def write_reports(self, relative_path, suite_name, reports,
                      package_name=None):
        """write the collection of reports to the given path"""

        dest_path = self.reserve_file(relative_path)
        with open(dest_path, 'wb') as outf:
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
