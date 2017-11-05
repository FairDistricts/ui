import numpy as np
import holoviews as hv
import geoviews as gv
import datashader as ds
import dask.dataframe as dd
from cartopy import crs

from bokeh.models import WMTSTileSource
from holoviews.operation.datashader import datashade

# Get renderer and set global display options
renderer = hv.extension('bokeh')
hv.opts("RGB [width=1200 height=682 xaxis=None yaxis=None show_grid=False]")
hv.opts("Polygons (fill_color=None line_width=1.5) [apply_ranges=False tools=['tap']]")
hv.opts("Points [apply_ranges=False] WMTS (alpha=0.5)")

# Load census data
df = dd.io.parquet.read_parquet('data/census.snappy.parq').persist()
census_points = gv.Points(df, kdims=['easting', 'northing'], vdims=['race'])

# Declare colormapping
color_key = {'w':'blue',  'b':'green', 'a':'red',   'h':'orange',   'o':'saddlebrown'}
races     = {'w':'White', 'b':'Black', 'a':'Asian', 'h':'Hispanic', 'o':'Other'}
color_points = hv.NdOverlay({races[k]: gv.Points([0,0], crs=crs.PlateCarree())(style=dict(color=v))
                             for k, v in color_key.items()})

# Apply datashading to census data
x_range, y_range = ((-13884029.0, -7453303.5), (2818291.5, 6335972.0)) # Continental USA
shade_defaults = dict(x_range=x_range, y_range=y_range, x_sampling=10, y_sampling=10, width=1200, height=682,
                      color_key=color_key, aggregator=ds.count_cat('race'),)
shaded = datashade(census_points, **shade_defaults)

# Load congressional districts
shape_path = 'data/cb_2015_us_cd114_5m/cb_2015_us_cd114_5m.shp'
districts = gv.Shape.from_shapefile(shape_path, crs=crs.PlateCarree())
districts = gv.operation.project_shape(districts)
districts = hv.Polygons([gv.util.geom_to_array(dist.data) for dist in districts])

# Define tile source
tile_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{Y}/{X}.jpg'
tiles = gv.WMTS(WMTSTileSource(url=tile_url))


# Render plot to bokeh document
plot = tiles * shaded * color_points * districts
doc = hv.renderer('bokeh').server_doc(plot)
