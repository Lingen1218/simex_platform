##########################################################################
#                                                                        #
# Copyright (C) 2016 Carsten Fortmann-Grote                              #
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

""" Module that holds the PlasmaXRTSCalculator class.

    @author : CFG
    @institution : XFEL
    @creation 20160225

"""
import h5py
import os
import re
import numpy
import subprocess
from SimEx.Calculators.AbstractPhotonDiffractor import AbstractPhotonDiffractor
from SimEx.Utilities.EntityChecks import checkAndSetInstance, checkAndSetPositiveInteger

from SimEx.Parameters.AbstractCalculatorParameters import AbstractCalculatorParameters

class PlasmaXRTSCalculator(AbstractPhotonDiffractor):
    """
    Class representing a plasma x-ray Thomson scattering calculation.
    """

    def __init__(self,  parameters=None, input_path=None, output_path=None):
        """
        Constructor for the PlasmaXRTSCalculator.

        @param parameters : Parameters for the PlasmaXRTSCalculator.
        @type : dict
        @default : None
        """

        # Check parameters.
        parameters = checkAndSetParameters( parameters )

        # Init base class.
        super( PlasmaXRTSCalculator, self).__init__(parameters, input_path, output_path)

        # Set state to not-initialized (e.g. input deck is not written).
        self.__is_initialized = False

        # Overwrite provided_data.
        self.__expected_data = ['/data/snp_<7 digit index>/ff',
                                '/data/snp_<7 digit index>/halfQ',
                                '/data/snp_<7 digit index>/Nph',
                                '/data/snp_<7 digit index>/r',
                                '/data/snp_<7 digit index>/T',
                                '/data/snp_<7 digit index>/Z',
                                '/data/snp_<7 digit index>/xyz',
                                '/data/snp_<7 digit index>/Sq_halfQ',
                                '/data/snp_<7 digit index>/Sq_bound',
                                '/data/snp_<7 digit index>/Sq_free',
                                '/history/parent/detail',
                                '/history/parent/parent',
                                '/info/package_version',
                                '/info/contact',
                                '/info/data_description',
                                '/info/method_description',
                                '/version']

        self.__provided_data = [
                                '/data/',
                                '/data/dynamic'
                                '/data/dynamic/energy_shifts',
                                '/data/dynamic/Skw_free',
                                '/data/dynamic/Skw_bound',
                                '/data/dynamic/collision_frequency',
                                '/data/static'
                                '/data/static/Sk_bound',
                                '/data/static/Sk_ion',
                                '/data/static/Sk_elastic',
                                '/data/static/Sk_core_inelastic',
                                '/data/static/Sk_free_inelastic',
                                '/data/static/Sk_total',
                                '/data/static/fk',
                                '/data/static/qk',
                                '/data/static/ionization_potential_delta'
                                '/data/static/LFC',
                                '/history/parent/detail',
                                '/history/parent/parent',
                                '/info/package_version',
                                '/info/contact',
                                '/info/data_description',
                                '/info/method_description',
                                '/info/units/energy'
                                '/info/units/structure_factor'
                                '/params/beam/photonEnergy',
                                '/params/beam/spectrum',
                                '/params/info',
                                ]

        self._input_data = {}

    def expectedData(self):
        """ Query for the data expected by the Diffractor. """
        return self.__expected_data

    def providedData(self):
        """ Query for the data provided by the Diffractor. """
        return self.__provided_data

    def backengine(self):
        """ This method drives the backengine xrts."""

        # Serialize the parameters (generate the input deck).
        self.parameters._serialize()

        # Write the spectrum if required.
        ### TODO

        # cd to the temporary directory where input deck was written.
        pwd = os.getcwd()

        # Setup command sequence and issue the system call.
        # Make sure to cd to correct directory where input deck is located.
        command_sequence = ['xrs']
        process = subprocess.Popen( command_sequence, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.parameters._tmp_dir )

        # Catch stdout and stderr, wait until process terminates.
        out, err = process.communicate(input=None)

        # Error handling.
        if not err == "":
            raise( RuntimeError, "Error during xrts backengine execution in %s. Error output follows. %s" % ( self.parameters._tmp_dir, err) )
        # Check if data was produced.
        path_to_data = os.path.join( self.parameters._tmp_dir, 'xrts_out.txt' )
        if not os.path.isfile( path_to_data ):
            raise( IOError, "No data generated. Check input deck %s." % ( os.path.join( self.parameters._tmp_dir, 'input.dat' ) ) )

        # Store output internally.
        self.__run_log = out

        # Write to tmp_dir.
        with open( os.path.join( self.parameters._tmp_dir ,'xrts.log'), 'w') as log_file_handle:
                log_file_handle.write(out)

        # Store data internally.
        self.__run_data = numpy.loadtxt( path_to_data )
        # Cd back to where we came from.
        os.chdir( pwd )


    @property
    def data(self):
        """ Query for the field data. """
        return self.__data

    def _readH5(self):
        """ """
        """ Private method for reading the hdf5 input and extracting the parameters and data relevant to initialize the object. """

        # Open the h5 file.
        h5 = h5py.File(self.input_path, 'r')

        self._input_data = {}
        self._input_data['source_spectrum'] = numpy.array(h5['misc/spectrum0'].value)

        h5.close()

    def saveH5(self):
        """ """
        """
        Method to save the data to a file.

        @param output_path : The file where to save the object's data.
        @type : string
        @default : None
        """

        # Setup h5 data groups and sets.
        h5 = h5py.File( self.output_path, 'w' )
        # Data
        h5.create_group("/data/dynamic")
        h5.create_group("/data/static")

        # History
        h5.create_group("/history/parent")

        # Info
        h5.create_group("/info/units/")

        # Parameters
        h5.create_group("/params/beam")


        # Create data datasets.
        # Dynamic data.
        energies  = self.__run_data[:,0]
        Skw_free  = self.__run_data[:,1]
        Skw_bound = self.__run_data[:,2]
        Skw_total = self.__run_data[:,3]
        ### TODO
        #collfreq  = self.__run_data[:,4]

        energy_shifts = h5.create_dataset("data/dynamic/energy_shifts", data=energies)
        energy_shifts.attrs.create('unit', 'eV')

        Skw_free = h5.create_dataset("data/dynamic/Skw_free", data=Skw_free)
        Skw_free.attrs.create('unit', 'eV**-1')

        Skw_bound = h5.create_dataset("data/dynamic/Skw_bound", data=Skw_bound)
        Skw_bound.attrs.create('unit', 'eV**-1')

        Skw_total = h5.create_dataset("data/dynamic/Skw_total", data=Skw_total)
        Skw_total.attrs.create('unit', 'eV**-1')

        # Static data.
        self.__static_data = parseStaticData( self.__run_log )

        # Save to h5 file.
        for key, value in self.__static_data.items():
            h5.create_dataset("/data/static/%s" % (key), data=value)

        # Attach a unit to the ionization potential lowering.
        h5['/data/static/']['ipl'].attrs.create('unit', 'eV')


                                #'/history/parent/detail',
                                #'/history/parent/parent',
                                #'/info/package_version',
                                #'/info/contact',
                                #'/info/data_description',
                                #'/info/method_description',
                                #'/params/beam/photonEnergy',
                                #'/params/beam/spectrum',
                                #'/params/info',
        ####
        # Close the file.
        ####
        h5.close()
        # Never write after this line in this function.

def parseStaticData(data_string):
        """
        Function to parse the run log and extract static data (form factors etc.)

        @params data_string : The string to parse.
        @type : str
        @return: A dictionary with static data.
        @rtype : dict

        """
        # Setup return dictionary.
        static_dict = {}

        # Extract static data from
        static_dict['fk']           = extractDate("f\(k\)\\s+=\\s\\d+\.\\d+", data_string)
        static_dict['qk']           = extractDate("q\(k\)\\s+=\\s\\d+\.\\d+", data_string)
        static_dict['Sk_ion']       = extractDate("S_ii\(k\)\\s+=\\s\\d+\.\\d+", data_string)
        static_dict['Sk_free']      = extractDate("S_ee\^0\(k\)\\s+=\\s\\d+\.\\d+", data_string)
        static_dict['Sk_core']      = extractDate("Core_inelastic\(k\)\\s+=\\s\\d+\.\\d+", data_string)
        static_dict['Wk']           = extractDate("Elastic\(k\)\\s+=\\s\\d+\.\\d+", data_string)
        static_dict['Sk_total']     = extractDate("S_total\(k\)\\s+=\\s\\d+\.\\d+", data_string)
        static_dict['ipl']          = extractDate("IP depression \[eV\]\\s+=\\s\\d+\.\\d+", data_string)
        static_dict['lfc']          = extractDate("G\(k\)\\s+=\\s\\d+\.\\d+", data_string)
        static_dict['debye_waller'] = extractDate("Debye-Waller\\s+=\\s+[1|\\d+.\\d+]", data_string)

        return static_dict


def extractDate(pattern_string, text):
    """ Workhorse function to get a pattern from text using a regular expression.
    @param pattern_string : The regex pattern to find.
    @type : str (argument to re.compile)

    @param text : The string from which to extract the date.
    @type : str

    @return : The date.
    @rtype : float
    """

    # Find the line.
    pattern = re.compile(pattern_string)
    line = pattern.findall(text)

    # Extract value (behind the '=' symbol).
    pattern = re.compile("=\\s")
    return  float( pattern.split( line[0] )[-1] )

###########################
# Check and set functions #
###########################
def checkAndSetParameters( parameters ):
    """ Utility to check if the parameters dictionary is ok ."""

    if not isinstance( parameters, AbstractCalculatorParameters ):
        raise RuntimeError( "The 'parameters' argument must be of the type PlasmaXRTSCalculatorParameters.")
    return parameters
