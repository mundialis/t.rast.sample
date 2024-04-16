MODULE_TOPDIR = ../../

PGM = t.rast.sample

include $(MODULE_TOPDIR)/include/Make/Script.make

python-requirements:
	pip install -r requirements.txt

default: python-requirements script $(TEST_DST)
