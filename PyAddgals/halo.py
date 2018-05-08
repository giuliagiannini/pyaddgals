from __future__ import print_function, division
from halotools.sim_manager import TabularAsciiReader


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

        if self.nbody.domain.fmat == 'BCCLightcone':
            self.readRockstarLightconeFile()

    def delete(self):
        """Delete halo catalog

        Returns
        -------
        None

        """

        for k in self.catalog.keys():
            del self.catalog[k]

    def getColumnDict(self, fmat):

        if fmat=='BCCLightcone':
            return {'mass':(2,np.float), 'x':(8,np.float), 'y':(9,np.float),
                        'z':(10,np.float), 'vx':(11,np.float),
                        'vy':(12,np.float), 'vz':(13,np.float),
                        'rs':(6,np.float), 'radius':(5,np.float),
                        'pid':(14,np.int)}
        else:
            raise(NotImplementedError("fmat {} not recognized".format(fmat)))


    def readRockstarLightconeFile(self):

        cdict = self.getColumnDict(self.nbody.domain.fmat)

        reader  = TabularAsciiReader(self.nbody.halofile, cdict)
        catalog = reader.read_ascii()
        names   = catalog.dtype.names

        #get the part of the catalog for this task
        r       = np.sqrt(catalog['x']**2 + catalog['y']**2 + catalog['z']**2)
        pix     = hp.vec2pix(self.nbody.domain.nside, catalog['x'],
                                catalog['y'], catalog['z'],
                                nest=self.nbody.domain.nest)
        idx      = (self.nbody.domain.rmin < r) & (r <= self.nbody.domain.rmax)
        idx      = (self.nbody.domain.pix == pix) & idx
        catalog  = catalog[idx]
        r        = r[idx]

        del idx

        self.catalog = {}

        ind = [names.index(c) for c in ['x','y','z']]
        self.catalog['pos'] = catalog.view((np.float,len(cdict.keys())))[:,ind]

        ind = [names.index(c) for c in ['vx','vy','vz']]
        self.catalog['vel'] = catalog.view((np.float,len(cdict.keys())))[:,ind]

        self.catalog['pid']    = catalog['pid']
        self.catalog['mass']   = catalog['mass']
        self.catalog['radius'] = catalog['radius'] / 1000. #convert kpc to mpc
        self.catalog['rs']     = catalog['rs'] / 1000. #convert kpc to mpc

        #calculate z from r
        self.catalog['z']     = cosmo.zofR(r)

        del r