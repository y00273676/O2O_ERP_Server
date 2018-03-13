import unittest
import tornado.testing
from tornado.options import options, define

from glob import glob


def all():
    test_modules = list(map(lambda x: x[:-3].replace('/', '.'),
                            glob('tests/*.py') + glob('tests/**/*.py')))

    print(test_modules)
    if options.case:
        test_modules = list(filter(lambda x: x.find(options.case)>0, test_modules))

    print(test_modules)
    return unittest.defaultTestLoader.loadTestsFromNames(test_modules)


if __name__ == "__main__":
    tornado.testing.main()
