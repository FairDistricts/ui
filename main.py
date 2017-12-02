import json
import re

import pandas as pd
from sqlalchemy import create_engine
import requests

import param
import parambokeh
import holoviews as hv
import geoviews as gv
import datashader as ds
import dask.dataframe as dd
from cartopy import crs

from bokeh.models import WMTSTileSource
from holoviews.operation.datashader import datashade

# Get renderer and set global display options
width = 1200
height = 600
hv.extension('bokeh')
hv.opts("RGB [width={width} height={height} xaxis=None yaxis=None show_grid=False]".format(width=width, height=height))
hv.opts("Polygons (fill_color=None line_width=1.5) [apply_ranges=False tools=['tap']]")
hv.opts("Points [apply_ranges=False] WMTS (alpha=0.5)")


# Load census data
df = dd.io.parquet.read_parquet('data/census.snappy.parq').persist()
census_points = gv.Points(df, kdims=['easting', 'northing'], vdims=['race'])

# Declare colormapping
color_key = {'w': 'purple',  'b': 'green', 'a': 'red',
             'h': 'orange',   'o': 'saddlebrown'}
races = {'w': 'White', 'b': 'Black', 'a': 'Asian',
         'h': 'Hispanic', 'o': 'Other'}
color_points = hv.NdOverlay({races[k]: gv.Points([0,0], crs=crs.PlateCarree())(style=dict(color=v))
                             for k, v in color_key.items()})

shapefile = {'state_house': 'cb_2016_48_sldl_500k',
             'state_senate': 'cb_2016_48_sldu_500k',
             'us_house': 'cb_2015_us_cd114_5m'}


# Define tile source
tile_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{Y}/{X}.jpg'
tiles = gv.WMTS(WMTSTileSource(url=tile_url))

x_range, y_range = ((-13884029.0, -7453303.5), (2818291.5, 6335972.0))  # Continental USA
shade_defaults = dict(x_range=x_range, y_range=y_range, x_sampling=10,
                        y_sampling=10, width=width, height=height,
                        color_key=color_key, aggregator=ds.count_cat('race'),)
shaded = datashade(census_points, **shade_defaults)

DIVISION_ID_RE = {
    'state_house': re.compile(r'ocd-division/country:us/state:[a-z]{2}/sldl:([0-9]+)'),
    'state_senate': re.compile(r'ocd-division/country:us/state:[a-z]{2}/sldu:([0-9]+)'),
    'us_house': re.compile(r'ocd-division/country:us/state:[a-z]{2}/cd:([0-9]+)'),
    'county': re.compile(r'ocd-division/country:us/state:[a-z]{2}/county:[^\/]+/council_district:([0-9]+)'),
    'city_council': re.compile(r'ocd-division/country:us/state:[a-z]{2}/place:[^\/]+/council_district:([0-9]+)'),
}


# engine = create_engine('mysql+mysqlconnector://atxhackathon:atxhackathon@atxhackathon.chs2sgrlmnkn.us-east-1.rds.amazonaws.com:3306/atxhackathon', echo=False)
# cnx = engine.raw_connection()
# vtd_data = pd.read_sql('SELECT * FROM vtd2016preselection', cnx)


def address_latlon_lookup(address, api_key):
    json_response = requests.get(
        'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'.format(
            address=address, api_key=api_key))
    # TODO: error handling for not found addresses
    #  result comes out looking like {"lat" : 30.2280933, "lng" : -97.8503729}
    location = json.loads(json_response)['results'][0]['geometry']['location']
    return location['lat'], location['lng']


def address_district_lookup(address, district_type, api_key):
    json_response = requests.get(
        'https://www.googleapis.com/civicinfo/v2/representatives?address={address}&key={api_key}'.format(
            address=address, api_key=api_key)
    )
    # TODO: error handling for not found addresses
    divisions = json.loads(json_response)['divisions']
    for key in divisions:
        match = DIVISION_ID_RE[district_type].match(key)
        if match:
            district = match.group(1)
    # TODO: error handling for no matching RE (maybe due to different state expression)
    return district


class DistrictExplorer(hv.streams.Stream):
    district_type = param.ObjectSelector(objects=('US House',
                                                  'State House',
                                                  'State Senate'),
                                         default='US House')

    def __init__(self, *args, **kwargs):
        super(DistrictExplorer, self).__init__(*args, **kwargs)
        self.plot = self.make_view()

    def load_district_shapefile(self, district_type, **kwargs):
        district_type = '_'.join([part.lower() for part in district_type.split()])
        shape_path = 'data/{0}/{0}.shp'.format(shapefile[district_type])
        districts = gv.Shape.from_shapefile(shape_path, crs=crs.PlateCarree())
        self.districts = gv.operation.project_shape(districts)
        return hv.Polygons([gv.util.geom_to_array(dist.data) for dist in self.districts])

    def make_view(self, **kwargs):
        districts = hv.DynamicMap(self.load_district_shapefile, streams=[self])

        options = dict(width=width, height=height, xaxis=None, yaxis=None,
                       show_grid=False)
        tiles.opts(plot=options)
        plot = tiles * shaded * color_points * districts
        plot.redim.range(easting=x_range, northing=y_range,
                         x=x_range, y=y_range)
        return plot

    def event(self, **kwargs):
        if self.district_type == 'US House':
            x_range, y_range = ((-13884029.0, -7453303.5), (2818291.5, 6335972.0))  # Continental USA
        else:
            x_range, y_range = self.districts.range(1), self.districts.range(2)
        self.plot.redim.range(easting=x_range, northing=y_range,
                              x=x_range, y=y_range)
        return super(DistrictExplorer, self).event(**kwargs)


explorer = DistrictExplorer(name="District explorer")
plot = hv.renderer('bokeh').instance(mode='server').get_plot(explorer.plot)
parambokeh.Widgets(explorer, continuous_update=True, callback=explorer.event,
                   on_init=True, plots=[plot.state], mode='server')
