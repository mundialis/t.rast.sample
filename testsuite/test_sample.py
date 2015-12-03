"""Test t.rast.sample

(C) 2015 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule

class TestRasterSample(TestCase):

    @classmethod
    def setUpClass(cls):
        """Initiate GIS and set the region
        """
        cls.use_temp_region()
        cls.runModule("g.region",  s=0,  n=80,  w=0,  e=120,  b=0,  t=50,  res=10,  res3=10)

        cls.runModule("r.mapcalc", expression="a_1 = 100",  overwrite=True)
        cls.runModule("r.mapcalc", expression="a_2 = 200",  overwrite=True)
        cls.runModule("r.mapcalc", expression="a_3 = 300",  overwrite=True)
        cls.runModule("r.mapcalc", expression="a_4 = 400",  overwrite=True)
        
        cls.runModule("v.random", output="points", npoints=3, seed=1, overwrite=True)

        cls.runModule("t.create",  type="strds",  temporaltype="absolute",  
                                 output="A",  title="A test",  description="A test",  
                                 overwrite=True)
        cls.runModule("t.register",  flags="i",  type="raster",  input="A",  
                                     maps="a_1,a_2,a_3,a_4",  start="2001-01-01", 
                                     increment="3 months",  overwrite=True)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region
        """
        cls.runModule("t.remove",  flags="rf",  type="strds",  
                                   inputs="A")
        cls.del_temp_region()


class TestRasterSampleFails(TestCase):

    def test_error_handling(self):
        # No vector map, no strds
        self.assertModuleFail("t.rast.sample",  output="out.txt")
        # No vector map
        self.assertModuleFail("t.rast.sample",  strds="A",  output="out.txt")

if __name__ == '__main__':
    from grass.gunittest.main import test
    test()
