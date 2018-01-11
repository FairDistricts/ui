District mapping UI
===========================

This is a bokeh app designed to facilitate exploration of demographic data in
the context of district representation and legislative outcomes. In creating
this app, our goals have been to present tools that tie data from many disparate
sources together, and unify it in geospatial context. In doing so, we hope to
provide people with perspective both on how their opinions are not being
represented, and how hostile gerrymandering is to their ability to do something
about that lack of representation.

![screenshot](/screenshot.png?raw=true "UI screenshot")

Installation
--------------

The conda package ecosystem is utilized heavily by this project. If you don't
yet have conda, you can get a barebones installation with Miniconda.
Instructions are at https://conda.io/miniconda.html

With a conda installation, create an environment with some prerequisites:

```
conda create -n mapping python=3.6 bokeh pandas fastparquet python-snappy sqlalchemy mysql-connector-python
```

Not all of our prerequisites are available from the default software channels.
We get a few more things from the conda-forge and ioam organizations on
anaconda.org:

```
conda install -n mapping -c ioam -c conda-forge notebook holoviews geoviews datashader parambokeh
```

Activate this environment, so that the Python environment we've created is the
one we'll use to run the bokeh web app:

```
source activate mapping
```

Download the data from:

* http://s3.amazonaws.com/datashader-data/census.snappy.parq.zip
* http://www2.census.gov/geo/tiger/GENZ2015/shp/cb_2015_us_cd114_5m.zip

The demographic data in the first link comes from
http://demographics.coopercenter.org/racial-dot-map/ and was captured in a
parquet file using instructions at
https://github.com/bokeh/datashader/issues/129

Extract it into a folder named ``data`` at the same level as main.py from this
github repo. You don't need to follow this path structure exactly, but if you
don't, you'll need to adjust paths in main.py.

The folder structure when fully extracted looks like:

```
data/cb_2015_us_cd114_5m:
cb_2015_us_cd114_5m.cpg            cb_2015_us_cd114_5m.prj            cb_2015_us_cd114_5m.shp.ea.iso.xml cb_2015_us_cd114_5m.shp.xml        cb_2015_us_cd114_5m.zip
cb_2015_us_cd114_5m.dbf            cb_2015_us_cd114_5m.shp            cb_2015_us_cd114_5m.shp.iso.xml    cb_2015_us_cd114_5m.shx

data/census.snappy.parq:
_common_metadata _metadata        part.0.parquet   part.1.parquet   part.2.parquet   part.3.parquet
```

Running the app
-----------------

Bokeh includes a standalone server. For simplicity and self-containment of this
repository, that's what we'll demonstrate.

In the folder containing main.py, run

```
bokeh serve .
```

You'll see output like:

```
2017-11-04 20:52:54,962 Starting Bokeh server version 0.12.10 (running on Tornado 4.5.2)
2017-11-04 20:52:54,966 Bokeh app running at: http://localhost:5006/mapping
2017-11-04 20:52:54,966 Starting Bokeh server with process id: 42539
```

Open your browser, and take a look at http://localhost:5006/mapping - have fun.

Beyond bokeh's built-in server, there are many other ways to deploy. These are
documented at http://bokeh.pydata.org/en/latest/docs/user_guide/server.html


TODO
----

* Docker image with mounted data dir
* Dataset discovery (rather than hardcoding)
* Additional widgets and metrics 
  * efficiency gap
  * compactness
  * per-district wasted votes
  * spatially plot which rep voted for what (to show in context of population)
* Tie in legislative data from https://github.com/FairDistricts/data-etl
* Add VTD-level election outcomes, to be displayed with or in place of census data
* Document user interactions

Credits
--------

This mapping app is based on prior work by Philipp Rudiger and Jim Bednar for
demonstrating the capabilities of their holoviews and datashader libraries.
