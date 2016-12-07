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

        cls.runModule("r.mapcalc", expression="a_1 = 100 + col() + row()",  overwrite=True)
        cls.runModule("r.mapcalc", expression="a_2 = 200 + col() + row()",  overwrite=True)
        cls.runModule("r.mapcalc", expression="a_3 = 300 + col() + row()",  overwrite=True)
        cls.runModule("r.mapcalc", expression="a_4 = 400 + col() + row()",  overwrite=True)

        cls.runModule("v.random", output="points", npoints=3, seed=1, overwrite=True)
        cls.runModule("v.out.ascii", input="points")

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

    def test_sampling(self):
        """Test the sampling

        :return:
        """
        self.assertModule("t.rast.sample",  points="points", strds="A",
                          output="out.txt",
                          flags="n", overwrite=True)

        content = """start_time|end_time|1|2|3
2001-01-01 00:00:00|2001-04-01 00:00:00|117|112|111
2001-04-01 00:00:00|2001-07-01 00:00:00|217|212|211
2001-07-01 00:00:00|2001-10-01 00:00:00|317|312|311
2001-10-01 00:00:00|2002-01-01 00:00:00|417|412|411
"""
        out = open("out.txt", "r").read()
        self.assertEqual(content, out)

    def test_sampling_no_header(self):
        """Test the sampling

        :return:
        """
        self.assertModule("t.rast.sample",  points="points", strds="A",
                          output="out.txt", overwrite=True)

        content = """2001-01-01 00:00:00|2001-04-01 00:00:00|117|112|111
2001-04-01 00:00:00|2001-07-01 00:00:00|217|212|211
2001-07-01 00:00:00|2001-10-01 00:00:00|317|312|311
2001-10-01 00:00:00|2002-01-01 00:00:00|417|412|411
"""
        out = open("out.txt", "r").read()
        self.assertEqual(content, out)

    def test_sampling_region(self):
        """Test the sampling

        :return:
        """
        self.runModule("g.region",  s=-10,  n=0,  w=-10,  e=0,  b=0,  t=50,  res=10,  res3=10)
        self.assertModule("t.rast.sample",  points="points", strds="A",
                          output="out.txt", flags="rn", overwrite=True)

        content = """start_time|end_time|1|2|3
2001-01-01 00:00:00|2001-04-01 00:00:00|117|112|111
2001-04-01 00:00:00|2001-07-01 00:00:00|217|212|211
2001-07-01 00:00:00|2001-10-01 00:00:00|317|312|311
2001-10-01 00:00:00|2002-01-01 00:00:00|417|412|411
"""
        out = open("out.txt", "r").read()
        self.assertEqual(content, out)

    def test_sampling_region_coords(self):
        """Test the sampling

        :return:
        """
        # cls.runModule("g.region",  s=0,  n=80,  w=0,  e=120,  b=0,  t=50,  res=10,  res3=10)
        self.runModule("g.region",  s=-10,  n=0,  w=-10,  e=0,  b=0,  t=50,  res=10,  res3=10)
        self.assertModule("t.rast.sample",  coordinates=[5,75,15,65,115,5], strds="A",
                          output="out.txt", flags="rn", overwrite=True)

        content = """start_time|end_time|3|2|1
2001-01-01 00:00:00|2001-04-01 00:00:00|120|104|102
2001-04-01 00:00:00|2001-07-01 00:00:00|220|204|202
2001-07-01 00:00:00|2001-10-01 00:00:00|320|304|302
2001-10-01 00:00:00|2002-01-01 00:00:00|420|404|402
"""
        out = open("out.txt", "r").read()
        self.assertEqual(content, out)


class TestRasterSampleFails(TestCase):

    def test_error_handling(self):
        # No vector map, no strds
        self.assertModuleFail("t.rast.sample",  output="out.txt", overwrite=True)
        # No vector map
        self.assertModuleFail("t.rast.sample",  strds="A",
                              output="out.txt", overwrite=True)

if __name__ == '__main__':
    from grass.gunittest.main import test
    test()
