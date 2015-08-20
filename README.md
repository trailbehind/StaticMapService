# StaticMaps

This service lets you render static maps, using Mapnik to style them.

It accepts GeoJSON POST requests, and returns a styled map, rendered on a background.

## Technology

This is designed to be used as a micro service and deployed as a Docker container.

It used Python, Django, and Mapnik.

## Prebuilt Docker Images

Prebuilt docker images available as gaiagps/staticmapservice, If you want to add your own background, extend that image. 

For an example service file for deploying with fleet see [staticmaps@.service](staticmaps@.service)

For an example of how to add your own backgrounds see [trailbehind/StaticMapService-extension-example](https://github.com/trailbehind/StaticMapService-extension-example/)
## API

### POST /{width}x{height}/{background}.{format}
#### Parameters
* width and height: Integer, greater than 0, max value defaults to 1024, but can be configured with the `MAX_IMAGE_DIMENSION` environment variable
* background: One of the installed background layers, or "none"

#### Post data - Required
GeoJSON data, with optional style data. Features and FeatureCollections are both supported.

##### Supported feature types
* Point
* Polygon
* LineString
* MultiLineString

MultiPoint, MultiPolygon and GeometryCollection features are not supported.

##### Styling

If a feature has a `style` element it will be used for styling, otherwise the `properties` element will be used for styling.

* Point features
Styling point features is not currently supported

* LineString features

    * `stroke` Stroke color, default is `red`
    * `stroke-width` stroke width, default is 2
    * `opacity` range is 0-1.0
    * `stroke-dasharray`
    * `stroke-linejoin` one of: `miter` `bevel` `round`
    * `stroke-linecap` one of `round` `butt` `square`
    * `smooth` line smoothing, range is 0-1.0

* Polygon features
    
    *  Polygons are stroked using the same styling options as LineString features
    * `fill` fill color, default is `red`
    * `opacity` fill opacity, default is 0.6

See [Mapnik LineSymbolizer reference](https://github.com/mapnik/mapnik/wiki/LineSymbolizer) and [Mapnik PolygonSymbolizer reference](https://github.com/mapnik/mapnik/wiki/PolygonSymbolizer) for more info.

### GET or POST /{bounds}/{width}x{height}/{background}.{format}
#### Parameters
* bounds: A bounding box in w,s,e,n format. Example `-120,38,-119,39`. Bounding boxes that cross the anti-meridian are not currently supported

#### Post data - Optional
* Same as above, but optional, and map will not be fit to data.

## Backgrounds
Backgrounds can be any file that can be read by mapnik using GDAL. One background is installed by default, 'OSM' which uses the GDAL WMS driver to load tiles from OpenStreetMap.org. Any file placed in the `staticMaps/baselayers/` directory is automatically loaded as a background/

## Attribution
Images can have attribution text overlayed on the image. Attribution is set per background layer, in the `staticMaps/baselayers/attribution.json` file.


## Example 
```bash
curl -X POST -H "Content-Type: application/json" -d \
 '{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"stroke":"#555555","stroke-width":2,"stroke-opacity":1,"fill":"#FED800","fill-opacity":0.5},"geometry":{"type":"Polygon","coordinates":[[[-122.49467253684996,37.77136775748373],[-122.49445796012878,37.771401680390476],[-122.49424338340759,37.77138471893906],[-122.493953704834,37.77131687309448],[-122.49380350112915,37.771189661968144],[-122.49377131462097,37.77101156602359],[-122.49380350112915,37.77079954648267],[-122.49388933181763,37.77067233446632],[-122.49405026435852,37.77057056469566],[-122.49428629875183,37.77054512223112],[-122.49451160430907,37.77062144959851],[-122.49474763870238,37.77079106568839],[-122.49483346939085,37.77102004679258],[-122.4948227405548,37.771223584956566],[-122.49467253684996,37.77136775748373]]]}},{"type":"Feature","properties":{"stroke-dasharray":[3,2]},"geometry":{"type":"LineString","coordinates":[[-122.49451160430907,37.77079954648267],[-122.4944633245468,37.77075290210209],[-122.49439358711244,37.77071473849609],[-122.49429166316986,37.77066809406202],[-122.49417901039122,37.770693536484245],[-122.49406099319457,37.77075714250155],[-122.49400734901428,37.77080378687947]]}},{"type":"Feature","geometry":{"type":"Point","coordinates":[-122.49448478221893,37.77111757556606]}},{"type":"Feature","geometry":{"type":"Point","coordinates":[-122.49414145946501,37.77113029670095]}}]}' \
 'http://192.168.99.100:8901/400x400/osm.png' > example.png
```

![Example image](http://static.gaiagps.com/staticMapsExample1.png)
