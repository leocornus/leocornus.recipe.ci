# testDoctests.py

from unittest import TestSuite 
from doctest import DocFileSuite
from doctest import ELLIPSIS
from doctest import NORMALIZE_WHITESPACE

from zc.buildout.testing import buildoutSetUp
from zc.buildout.testing import install_develop
from zc.buildout.testing import install
from zc.buildout.testing import buildoutTearDown

__author__ = "Sean Chen"
__email__ = "sean.chen@leocorn.com"

optionflags = (ELLIPSIS | NORMALIZE_WHITESPACE)

# set up the buildout testing enviroment.
def setUp(test):

    buildoutSetUp(test)
    install_develop('leocornus.recipe.ci', test)
    install('pexpect', test)
    install('mwclient', test)
    install('requests', test)
    install('six', test)
    install('ecdsa', test)
    install('pycrypto', test)

def test_suite():

    suite = TestSuite()
    suite.addTest(
        DocFileSuite(
            'README.rst',
            package='leocornus.recipe.ci',
            setUp=setUp,
            tearDown=buildoutTearDown,
            optionflags=optionflags,
            ),
        )

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
