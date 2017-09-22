""" :module DetectorGeometryParameters: Module holding the DetectorGeometryParameters class. """
##########################################################################
#                                                                        #
# Copyright (C) 2015-2017 Carsten Fortmann-Grote                         #
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

from SimEx.Parameters.AbstractCalculatorParameters import AbstractCalculatorParameters
from SimEx.Utilities.EntityChecks import checkAndSetInstance

import scipy
from scipy import constants
import os
import numpy
from wpg.srwlib import srwl
import math

from wpg import Wavefront, wpg_uti_wf

class DetectorGeometryParameters(AbstractCalculatorParameters):
    """ Class representing photon beam parameters. """

    def __init__(self,
            photon_energy,
            beam_diameter_fwhm,
            pulse_energy,
            photon_energy_relative_bandwidth=None,
            divergence=None,
            photon_energy_spectrum_type=None,
            **kwargs
            ):
        """
        Constructor of the DetectorGeometryParameters class.

        :param photon_energy: The mean photon energy in units of electonvolts (eV).
        :type photon_energy: float

        :param photon_energy_relative_bandwidth: The relative energy bandwidth
        :type photon_energy_relative_bandwidth: float (>0.0).

        :param beam_diameter_fwhm: Beam diameter in units of metre (m).
        :type beam_diameter_fwhm: float

        :param pulse_energy: Total energy of the pulse in units of Joule (J).
        :type pulse_energy: float

        :param divergence: Beam divergence angle in units of radian (rad).
        :type divergence: float (0 < divergence < 2*pi)

        :param photon_energy_spectrum_type: Type of energy spectrum ("SASE" | "tophat" | "twocolour", default "SASE").
        :type photon_energy_spectrum_type: float (0 < photon_energy_spectrum_type < 2*pi)

        :param kwargs: Key-value pairs to be passed to the parent class constructor.
        :type kwargs: dict

        """

        super(DetectorGeometryParameters, self).__init__(**kwargs)

        self.photon_energy = photon_energy
        self.photon_energy_relative_bandwidth = photon_energy_relative_bandwidth
        self.beam_diameter_fwhm = beam_diameter_fwhm
        self.pulse_energy = pulse_energy
        self.divergence = divergence
        self.photon_energy_spectrum_type = photon_energy_spectrum_type

    def _setDefaults(self):
        """ Set default for required inherited parameters. """
        self._AbstractCalculatorParameters__cpus_per_task_default = 1


    @property
    def photon_energy(self):
        """ Query the 'photon_energy' parameter. """
        return self.__photon_energy
    @photon_energy.setter
    def photon_energy(self, val):
        """ Set the 'photon_energy' parameter to val."""
        self.__photon_energy = checkAndSetInstance( float, val, None)

    @property
    def photon_energy_spectrum_type(self):
        """ Query the 'photon_energy_spectrum_type' parameter. """
        return self.__photon_energy_spectrum_type
    @photon_energy_spectrum_type.setter
    def photon_energy_spectrum_type(self, val):
        """ Set the 'photon_energy_spectrum_type' parameter to val."""
        self.__photon_energy_spectrum_type = checkAndSetInstance( str, val, "SASE")

    @property
    def photon_energy_relative_bandwidth(self):
        """ Query the 'photon_energy_relative_bandwidth' parameter. """
        return self.__photon_energy_relative_bandwidth
    @photon_energy_relative_bandwidth.setter
    def photon_energy_relative_bandwidth(self, val):
        """ Set the 'photon_energy_relative_bandwidth' parameter to val."""
        self.__photon_energy_relative_bandwidth = checkAndSetInstance( float, val, 0.01)

    @property
    def beam_diameter_fwhm(self):
        """ Query the 'beam_diameter_fwhm' parameter. """
        return self.__beam_diameter_fwhm
    @beam_diameter_fwhm.setter
    def beam_diameter_fwhm(self, val):
        """ Set the 'beam_diameter_fwhm' parameter to val."""
        self.__beam_diameter_fwhm = checkAndSetInstance( float, val, None)

    @property
    def divergence(self):
        """ Query the 'divergence' parameter. """
        return self.__divergence
    @divergence.setter
    def divergence(self, val):
        """ Set the 'divergence' parameter to val."""
        self.__divergence = checkAndSetInstance( float, val, 0.0)

    @property
    def pulse_energy(self):
        """ Query the 'pulse_energy' parameter. """
        return self.__pulse_energy
    @pulse_energy.setter
    def pulse_energy(self, val):
        """ Set the 'pulse_energy' parameter to val."""
        self.__pulse_energy = checkAndSetInstance( float, val, None)

def propToBeamParameters( prop_output_path ):
    """ Utility to setup a DetectorGeometryParameters instance from propagation output. """

    # Check prop out exists.
    if not os.path.isfile(prop_output_path):
        raise IOError("File not found: %s." % (prop_output_path) )

    # Construct the wavefront.
    wavefront = Wavefront()
    wavefront.load_hdf5( prop_output_path )

    pulse_energy = wpg_uti_wf.calc_pulse_energy( wavefront )

    mesh = wavefront.params.Mesh
    dx = (mesh.xMax - mesh.xMin)/(mesh.nx - 1)
    dy = (mesh.yMax - mesh.yMin)/(mesh.ny - 1)
    int0 = wavefront.get_intensity().sum(axis=0).sum(axis=0)  # I(slice_num)
    total_intensity = int0*dx*dy # [J]

    times = numpy.linspace(mesh.sliceMin, mesh.sliceMax, mesh.nSlices)

    t = times[:-1]
    dt = times[1:] - times[:-1]

    It = total_intensity[:-1]

    m0 = numpy.sum( It*dt)
    m1 = numpy.sum( It*t*dt )/m0
    m2 = numpy.sum( It*t**2*dt)/m0

    rms = math.sqrt(m2 - m1**2)

    spike_fwhm_J = constants.hbar/rms
    spike_fwhm_eV = spike_fwhm_J/constants.e

    # Switch to energy domain
    srwl.SetRepresElecField(wavefront._srwl_wf, 'f')

    mesh = wavefront.params.Mesh
    spectrum = wavefront.get_intensity().sum(axis=0).sum(axis=0)  # I(slice_num)
    energies = numpy.linspace(mesh.sliceMin, mesh.sliceMax, mesh.nSlices)

    w = energies[:-1]
    dw = energies[1:] - energies[:-1]

    Iw = spectrum[:-1]

    m0 = numpy.sum( Iw*dw)
    m1 = numpy.sum( Iw*w*dw )/m0
    m2 = numpy.sum( Iw*w**2*dw)/m0

    rms = math.sqrt(m2 - m1**2)

    photon_energy = m1
    spec_fwhm_eV = rms

    # Extract beam diameter fwhm
    xy_fwhm = wpg_uti_wf.calculate_fwhm(wavefront)

    # Extract divergence
    # Switch to reciprocal space
    srwl.SetRepresElecField(wavefront._srwl_wf, 'a')
    qxqy_fwhm = wpg_uti_wf.calculate_fwhm(wavefront)

    del wavefront

    beam_parameters = DetectorGeometryParameters(
            photon_energy=photon_energy,
            photon_energy_relative_bandwidth=spike_fwhm_eV/photon_energy,
            pulse_energy=pulse_energy,
            divergence=max([qxqy_fwhm['fwhm_x'],qxqy_fwhm['fwhm_y']])/2.,
            beam_diameter_fwhm=max([xy_fwhm['fwhm_x'],xy_fwhm['fwhm_y']]),
            photon_energy_spectrum_type="SASE",
            )

    print "photon_energy=%5.4f eV" % beam_parameters.photon_energy
    print "photon_energy_relative_bandwidth=", beam_parameters.photon_energy_relative_bandwidth
    print "pulse_energy=%4.3e J" % beam_parameters.pulse_energy
    print "divergence=%4.3e rad" % beam_parameters.divergence
    print "beam_diameter_fwhm=%4.3e m" % beam_parameters.beam_diameter_fwhm

    return beam_parameters

