##########################################################################
#                                                                        #
# Copyright (C) 2015 Carsten Fortmann-Grote                              #
# Contact: Carsten Fortmann-Grote <carsten.grote@xfel.eu>                #
#                                                                        #
# This file is part of simex_platform.                                   #
# simex_platform is free software: you can redistribute it and/or modify #
# it under the terms of the GNU General Public License as published by   #
# the Free Software Foundation, either version 3 of the License, or      #
# (at your option) any later version.                                    #
#                                                                        #
# simex_platform is distributed in the hope that it will be useful,      #
# but WITHOUT ANY WARRANTY; without even the implied warranty of         #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
# GNU General Public License for more details.                           #
#                                                                        #
# You should have received a copy of the GNU General Public License      #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
##########################################################################

""" Test module for the AbstractPhotonPropagator module.

    @author : CFG
    @institution : XFEL
    @creation 20151006

"""
import os

import paths
import unittest


# Import the class to test.
from SimEx.Calculators.AbstractPhotonPropagator import AbstractPhotonPropagator
from SimEx.Calculators.AbstractBaseCalculator import AbstractBaseCalculator

from TestUtilities import TestUtilities

class TestPhotonPropagator(AbstractPhotonPropagator):
    """ Implements a dummy child instance of the AbstractPhotonPropagator base class."""

    def __init__(self):
        super(TestPhotonPropagator, self).__init__(parameters=None, input_path=None, output_path=None)

    def backengine(self):
        pass

    def _readH5(self): pass
    def saveH5(self): pass


class AbstractPhotonPropagatorTest(unittest.TestCase):
    """
    Test class for the AbstractPhotonPropagator.
    """

    @classmethod
    def setUpClass(cls):
        """ Setting up the test class. """

    @classmethod
    def tearDownClass(cls):
        """ Tearing down the test class. """

    def setUp(self):
        """ Setting up a test. """
        self.test_class = TestPhotonPropagator()

    def tearDown(self):
        """ Tearing down a test. """
        del self.test_class

    def testConstruction(self):
        """ Testing the default construction of the class. """

        self.assertRaises(TypeError, AbstractPhotonPropagator )

    def testConstructionDerived(self):
        """ Test that we can construct a derived class and it has the correct inheritance. """
        test_source = self.test_class

        self.assertIsInstance( test_source, TestPhotonPropagator )
        self.assertIsInstance( test_source, object )
        self.assertIsInstance( test_source, AbstractBaseCalculator )
        self.assertIsInstance( test_source, AbstractPhotonPropagator )

    def testDataInterfaceQueries(self):
        """ Check that the data interface queries work. """

        # Get test instance.
        test_propagator = self.test_class

        # Get expected and provided data descriptors.
        expected_data = test_propagator.expectedData()
        provided_data = test_propagator.providedData()

        # Check types are correct.
        self.assertIsInstance(expected_data, list)
        self.assertIsInstance(provided_data, list)
        for d in expected_data:
            self.assertIsInstance(d, str)
            self.assertEqual(d[0], '/')
        for d in provided_data:
            self.assertIsInstance(d, str)
            self.assertEqual(d[0], '/')

    def testDefaultPaths(self):
        """ Check that default pathnames are chosen correctly. """

        propagator = TestPhotonPropagator()

        self.assertEqual(propagator.output_path, os.path.abspath('prop'))
        self.assertEqual(propagator.input_path, os.path.abspath('source'))




if __name__ == '__main__':
    unittest.main()

