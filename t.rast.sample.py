#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.sample
# AUTHOR(S):    Soeren Gebbert
#
# PURPOSE:      Sample a space time raster dataset at specific point
#               coordinates and write the output into a file or stdout
#
# COPYRIGHT:    (C) 2015 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (version 2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Sample a space time raster dataset at specific vector point coordinates and write the output into a file or stdout
#% keyword: temporal
#% keyword: raster
#% keyword: sampling
#% keyword: time
#%end

#%option G_OPT_V_INPUT
#% required: no
#% key: points
#%end

#%option G_OPT_M_COORDS
#% required: no
#% description: Comma separated list of coordinates
#%end

#%option G_OPT_STRDS_INPUT
#% key: strds
#%end

#%option G_OPT_F_OUTPUT
#% required: no
#% description: Name for the output file, stdout will be used if not specified
#%end

#%option G_OPT_T_WHERE
#%end

#%option G_OPT_F_SEP
#%end

#%option
#% key: column
#% type: string
#% description: The vector point column to be used as column header
#% required: no
#% answer: cat
#%end

#%option
#% key: order
#% type: string
#% description: Sort the maps by category
#% required: no
#% multiple: yes
#% options: id, name, creator, mapset, creation_time, modification_time, start_time, end_time, north, south, west, east, min, max
#% answer: start_time
#%end

#%flag
#% key: n
#% description: Output header row
#%end

#%flag
#% key: r
#% description: Use the raster region of each map for sampling
#%end


import grass.script as gscript
import grass.temporal as tgis
import grass.pygrass.vector as pyvect
import grass.pygrass.vector.geometry as pygeom
import grass.pygrass.raster as pyrast
import grass.pygrass.gis.region as pyregion
import grass.lib.vector as libvect
import grass.lib.raster as librast
import sys


STR_RTYPE = {'CELL':librast.CELL_TYPE,
             'FCELL':librast.FCELL_TYPE,
             'DCELL':librast.DCELL_TYPE}

class SamplePoint(object):
    def __init__(self, x, y, cat, column=None):
        self.x = x
        self.y = y
        self.cat = cat
        self.column = column
        self.value = None
    def __str__(self):
        return str(self.x) + " " + \
            str(self.y) + " " + \
            str(self.cat) + " " + \
            str(self.column)

    def coords(self):
        return (self.x, self.y)

###############################################################################


class SamplePointComparisonY(object):
    """This comparison key can be used to sort lists of SamplePoint
       by Y coordinate

        Example:

        .. code-block:: python

            # Sort the SamplePoint's in the list by Y coordinate
            sorted_p_list = sorted(p_list, key=SamplePointComparisonY)
    """
    def __init__(self, obj, *args):
        self.obj = obj

    def __lt__(self, other):
        return self.obj.y < other.obj.y

    def __gt__(self, other):
        return self.obj.y > other.obj.y

    def __eq__(self, other):
        return self.obj.y == other.obj.y

    def __le__(self, other):
        return self.obj.y <= other.obj.y

    def __ge__(self, other):
        return self.obj.y >= other.obj.y

    def __ne__(self, other):
        return self.obj.y != other.obj.y

############################################################################

def main(options, flags):

    # Get the options
    points = options["points"]
    strds = options["strds"]
    output = options["output"]
    where = options["where"]
    order = options["order"]
    column = options["column"]
    separator = options["separator"]
    coordinates = options["coordinates"]

    # Setup separator
    if separator == "pipe":
        separator = "|"
    if separator == "comma":
        separator = ","
    if separator == "space":
        separator = " "
    if separator == "tab":
        separator = "\t"
    if separator == "newline":
        separator = "\n"

    use_cats = False

    write_header = flags["n"]
    use_raster_region = flags["r"]

    overwrite = gscript.overwrite()

    if points and coordinates:
        gscript.fatal(_("points and coordinates are mutually exclusive"))

    if not points and not coordinates:
        gscript.fatal(_("You must specify points or coordinates"))

    # Make sure the temporal database exists
    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    sp = tgis.open_old_stds(strds, "strds", dbif)
    maps = sp.get_registered_maps_as_objects(where=where, order=order,
                                             dbif=dbif)
    dbif.close()

    if not maps:
        gscript.fatal(_("Space time raster dataset <%s> is empty") % sp.get_id())

    # The list of sample points
    p_list = []

    if not coordinates:
        # Check if the chosen header column is in the vector map
        vname = points
        vmapset= ""
        if "@" in points:
            vname, vmapset = points.split("@")

        v = pyvect.VectorTopo(vname, vmapset)
        v.open("r")

        col_index = 0

        if v.exist() == False:
            gscript.fatal(_("Vector map <%s> does not exist" %(points)))

        if not v.table:
            use_cats = True
            gscript.warning(_("Vector map <%s> does not have an attribute table, using cats as header column." %(points)))

        if v.table and column not in v.table.columns:
            gscript.fatal(_("Vector map <%s> has no column named %s" %(points, column)))

        if use_cats is False:
            col_index = list(v.table.columns.names()).index(column)

        # Create the point list
        for line in v:
            if line.gtype == libvect.GV_POINT:
                if use_cats is False:
                    p = SamplePoint(line.x, line.y, line.cat, line.attrs.values()[col_index])
                elif use_cats is True:
                    p = SamplePoint(line.x, line.y, line.cat)

                p_list.append(p)

        v.close()
    else:
        # Convert the coordinates into sample points
        coord_list = coordinates.split(",")
        use_cats = True

        count = 0
        cat = 1
        while count < len(coord_list):
            x = coord_list[count]
            count += 1
            y = coord_list[count]
            count += 1

            p = SamplePoint(float(x), float(y), cat)
            p_list.append(p)
            cat += 1

    if output:
        out_file = open(output, "w")
    else:
        out_file = sys.stdout

    # Write the header
    if write_header:
        out_file.write("start_time")
        out_file.write(separator)
        out_file.write("end_time")
        out_file.write(separator)
        count = 0
        for p in p_list:
            count += 1
            if use_cats is True:
                out_file.write(str(p.cat))
            else:
                out_file.write(str(p.column))
            if count != len(p_list):
                out_file.write(separator)
        out_file.write("\n")

    # Sorting the points by y-coordinate to make use of the single row cache and read direction
    sorted_p_list = sorted(p_list, key=SamplePointComparisonY)

    # Sample the raster maps
    num = 0
    for map in maps:
        num += 1
        sys.stderr.write("Sample map <%s> number  %i out of %i\n" %(map.get_name(), num, len(maps)))

        start, end = map.get_temporal_extent_as_tuple()
        out_file.write(str(start))
        out_file.write(separator)
        if not end:
            out_file.write(str(start))
        else:
            out_file.write(str(end))
        out_file.write(separator)

        r = pyrast.RasterRow(map.get_name(), map.get_mapset())
        if r.exist() == False:
            gscript.fatal(_("Raster map <%s> does not exist" %(map.get_id())))

        region = None
        if use_raster_region is True:
            r.set_region_from_rast()
            region = pyregion.Region()
            region.from_rast(map.get_name())
        # Open the raster layer after the region settings
        r.open("r")

        # Sample the raster maps with the sorted points
        for p in sorted_p_list:
            p.value = r.get_value(point=p, region=region)

        # Write the point values from the original list
        count = 0
        for p in p_list:
            count += 1
            out_file.write(str(p.value))
            if count != len(p_list):
                out_file.write(separator)
        out_file.write("\n")

        r.close()

    out_file.close()

############################################################################

if __name__ == "__main__":
    options, flags = gscript.parser()
    main(options, flags)
