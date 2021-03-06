from __future__ import print_function, division
from halotools.sim_manager import TabularAsciiReader
import numpy as np
import healpy as hp


class HaloCatalog(object):

    def __init__(self, nbody, **kwargs):
        """Short summary.

        Parameters
        ----------
        nbody : NBody
            The nbody this halo catalog belongs to. Contains information about how to read data, and the domain decomposition.
        **kwargs : type
            Description of parameter `**kwargs`.

        Returns
        -------
        None

        """

        self.nbody = nbody

    def read(self):

        if self.nbody.domain.fmt == 'BCCLightcone':
            self.readRockstarLightconeFile()
        elif self.nbody.domain.fmt == 'Snapshot':
            self.readRockstarSnapshotFile()

    def delete(self):
        """Delete halo catalog

        Returns
        -------
        None

        """

        if not hasattr(self, 'catalog'):
            return

        keys = list(self.catalog.keys())

        if len(keys) == 0:
            return

        for k in keys:
            del self.catalog[k]

    def getColumnDict(self, fmt):

        if fmt == 'BCCLightcone':
            return {'mass': (2, np.float), 'x': (8, np.float), 'y': (9, np.float),
                    'z': (10, np.float), 'vx': (11, np.float),
                    'vy': (12, np.float), 'vz': (13, np.float),
                    'rs': (6, np.float), 'radius': (5, np.float),
                    'pid': (14, np.int), 'id': (0, np.int)}

        elif fmt == 'Snapshot':
            return {'mass': (2, np.float), 'x': (8, np.float), 'y': (9, np.float),
                    'z': (10, np.float), 'vx': (11, np.float),
                    'vy': (12, np.float), 'vz': (13, np.float),
                    'rs': (6, np.float), 'radius': (5, np.float),
                    'pid': (14, np.int), 'id': (0, np.int)}
        elif fmt == 'OutLightcone':
            return {'HALOID': (0, np.int), 'HOST_HALOID': (1, np.int), 'MVIR': (2, np.float), 'VMAX': (3, np.float),
                    'VRMS': (4, np.float), 'RVIR': (5, np.float), 'RS': (6, np.float), 'NP': (7, np.float),
                    'PX': (8, np.float), 'PY': (9, np.float), 'PZ': (10, np.float), 'VX': (11, np.float),
                    'VY': (12, np.float), 'VZ': (13, np.float), 'JX': (14, np.float), 'JY': (15, np.float),
                    'JZ': (16, np.float), 'SPIN': (17, np.float), 'Z': (18, np.float), 'Z_COS': (19, np.float),
                    'M200B': (20, np.float), 'M200C': (21, np.float), 'M500C': (22, np.float),
                    'M2500C': (23, np.float), 'XOFF': (24, np.float), 'VOFF': (25, np.float),
                    'B_TO_A': (27, np.float), 'C_TO_A': (28, np.float), 'A[X]': (29, np.float),
                    'A[Y]': (30, np.float), 'A[Z]': (31, np.float), 'B[X]': (32, np.float),
                    'B[Y]': (33, np.float), 'B[Z]': (34, np.float), 'C[X]': (35, np.float), 'C[Y]': (36, np.float),
                    'C[Z]': (37, np.float), 'TRA': (38, np.float), 'TDEC': (39, np.float), 'RA': (40, np.float),
                    'DEC': (41, np.float)}

        else:
            raise(NotImplementedError("fmt {} not recognized".format(fmt)))

    def readRockstarLightconeFile(self):

        cdict = self.getColumnDict(self.nbody.domain.fmt)
        reader = TabularAsciiReader(
            self.nbody.halofile[self.nbody.boxnum], cdict)
        catalog = reader.read_ascii()
        names = catalog.dtype.names

        rnn = np.loadtxt(self.nbody.halodensfile[self.nbody.boxnum])

        # get the part of the catalog for this task
        r = np.sqrt(catalog['x']**2 + catalog['y']**2 + catalog['z']**2)
        pix = hp.vec2pix(self.nbody.domain.nside, catalog['x'],
                         catalog['y'], catalog['z'],
                         nest=self.nbody.domain.nest)
        idx = (self.nbody.domain.rmin < r) & (r <= self.nbody.domain.rmax)
        idx = (self.nbody.domain.pix == pix) & idx
        catalog = catalog[idx]
        r = r[idx]
        rnn = rnn[idx]

        del idx

        self.catalog = {}

        # calculate z from r
        self.catalog['z'] = self.nbody.cosmo.zofR(r)
        del r
        self.catalog['id'] = catalog['id']

        ind = [names.index(c) for c in ['x', 'y', 'z']]
        self.catalog['pos'] = catalog.view(
            (np.float, len(cdict.keys())))[:, ind]

        ind = [names.index(c) for c in ['vx', 'vy', 'vz']]
        self.catalog['vel'] = catalog.view(
            (np.float, len(cdict.keys())))[:, ind]

        self.catalog['pid'] = catalog['pid']
        self.catalog['mass'] = catalog['mass']
        self.catalog['radius'] = catalog['radius'] / \
            1000.  # convert kpc to mpc
        self.catalog['rs'] = catalog['rs'] / 1000.  # convert kpc to mpc
        self.catalog['rnn'] = rnn[:, 1]

    def readHaloRnn(self, filepath):
        """
        Read text output from calcRnn code for halos
        into numpy array

        """

        dtype = np.dtype([('id', int), ('delta', float)])
        delta = np.genfromtxt(filepath, dtype=dtype)
        return delta['delta']

    def readRockstarSnapshotFile(self):
        boxnum = self.nbody.boxnum
        nbox = self.nbody.domain.nbox[boxnum]

        snapnum = self.nbody.domain.snapnum
        if snapnum < 10:
            snapnum = '0{}'.format(snapnum)
        else:
            snapnum = '{}'.format(snapnum)

        cdict = self.getColumnDict(self.nbody.domain.fmt)

        halofile = self.nbody.halofile[self.nbody.boxnum].format(
            snapnum=snapnum)

        halornnfile = self.nbody.halodensfile[self.nbody.boxnum].format(
            snapnum=snapnum)

        reader = TabularAsciiReader(halofile, cdict)
        catalog = reader.read_ascii()
        names = catalog.dtype.names

        rnn = self.readHaloRnn(halornnfile)

        # get the part of the catalog for this task
        idxx = nbox * catalog['x'] // self.nbody.domain.lbox[boxnum]
        idxy = nbox * catalog['y'] // self.nbody.domain.lbox[boxnum]
        idxz = nbox * catalog['z'] // self.nbody.domain.lbox[boxnum]
        idx = idxx * nbox ** 2 + idxy * nbox + idxz
        idx = idx == self.nbody.domain.subbox

        catalog = catalog[idx]
        rnn = rnn[idx]

        del idx

        self.catalog = {}

        # calculate z from r
        self.catalog['z'] = np.zeros_like(rnn) + self.nbody.domain.zmean
        self.catalog['id'] = catalog['id']

        ind = [names.index(c) for c in ['x', 'y', 'z']]
        self.catalog['pos'] = catalog.view(
            (np.float, len(cdict.keys())))[:, ind]

        ind = [names.index(c) for c in ['vx', 'vy', 'vz']]
        self.catalog['vel'] = catalog.view(
            (np.float, len(cdict.keys())))[:, ind]

        self.catalog['pid'] = catalog['pid']
        self.catalog['mass'] = catalog['mass']
        self.catalog['radius'] = catalog['radius'] / \
            1000.  # convert kpc to mpc
        self.catalog['rs'] = catalog['rs'] / 1000.  # convert kpc to mpc
        self.catalog['rnn'] = rnn
