MODULE_TOPDIR = ../../

PGM = t.rast.sample

include $(MODULE_TOPDIR)/include/Make/Script.make

default: script $(TEST_DST)
