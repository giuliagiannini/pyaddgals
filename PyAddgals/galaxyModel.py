from __future__ import print_function, division
from abc import ABCMeta, abstractmethod
import numpy as np


class GalaxyModel(object):

    __metaclass__ = ABCMeta

    def __init__(self, nbody):
        self.nbody = nbody
        pass

    @abstractmethod
    def paintGalaxies(self):
        """Abstract method that populates the galaxyCatalog.catalog.

        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        self.catalog = None

    def drawRedshifts(self, n_gal):
        """Draw redshifts proportional to r^3

        Parameters
        ----------
        n_gal : int
            number of galaxies to draw redshifts for

        Returns
        -------
        z : np.array
            Array of length n_gal containing redshifts of the galaxies.

        """

        rmin = self.nbody.domain.rmin
        rmax = self.nbody.domain.rmax

        rands = np.random.uniform(size=n_gal)
        z = ((rmax ** 3 - rmin ** 3) * rands + rmin ** 3) ** (1 / 3)
        z = self.nbody.cosmo.zofR(z)

        return z
