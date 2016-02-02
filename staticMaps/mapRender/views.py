# coding=UTF-8
import cStringIO
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.contrib.gis.geos import LineString, MultiLineString, Point, Polygon
from django.contrib.gis.geos import GeometryCollection, GEOSGeometry
from django.conf import settings
import json
import logging
import mapnik
from math import log
import os
from PIL import Image, ImageDraw, ImageFont
import re
import urllib

IMAGE_FORMATS = ['png', 'png32', 'png64', 'png128', 'png256', 'jpeg', 'jpeg70', 'jpeg80', 'jpeg90']
try:
    LINEJOIN_OPTIONS = {
        'miter': mapnik.line_join.miter,
        'bevel': mapnik.line_join.bevel,
        'round': mapnik.line_join.round
    }
except:
    LINEJOIN_OPTIONS = {
        'miter': mapnik.stroke_linejoin.MITER_JOIN,
        'bevel': mapnik.stroke_linejoin.BEVEL_JOIN,
        'round': mapnik.stroke_linejoin.ROUND_JOIN
    }

try:
    LINECAP_OPTIONS = {
        'round': mapnik.line_cap.round,
        'butt': mapnik.line_cap.butt,
        'square': mapnik.line_cap.square
    }
except:
    LINECAP_OPTIONS = {
        'round': mapnik.stroke_linecap.ROUND_CAP,
        'butt': mapnik.stroke_linecap.BUTT_CAP,
        'square': mapnik.stroke_linecap.SQUARE_CAP
    }

class InvalidStyleException(Exception):
    """ """


def render_static(request, height=None, width=None, format='png',
                  background='satellite', bounds=None, center=None, render_srid=3857):

# width and height
    width = int(width)
    height = int(height)
    if width > settings.MAX_IMAGE_DIMENSION or \
        height > settings.MAX_IMAGE_DIMENSION or \
        width <= 1 or height <= 1:
        logging.debug("Invalid size")
        return HttpResponseBadRequest("Invalid image size, both dimensions must be in range %i-%i" % (1, settings.MAX_IMAGE_DIMENSION))

# image format
    if format not in IMAGE_FORMATS:
        logging.error("unknown image format %s" % format)
        return HttpResponseBadRequest("Unknown image format, available formats: " + ", ".join(IMAGE_FORMATS))

    if format.startswith('png'):
        mimetype = 'image/png'
    elif format.startswith('jpeg'):
        mimetype = 'image/jpeg'

# bounds
    bounds_box = None
    if bounds:
        bounds_components = bounds.split(',')
        if len(bounds_components) != 4:
            return HttpResponseBadRequest("Invalid bounds, must be 4 , separated numbers")
        bounds_components = [float(f) for f in bounds_components]

        if not (-180 < bounds_components[0] < 180) or not (-180 < bounds_components[2] < 180):
            logging.error("x out of range %f or %f" % (bounds_components[0], bounds_components[2]))
            return HttpResponseBadRequest("x out of range %f or %f" % (bounds_components[0], bounds_components[2]))
        if not (-90 < bounds_components[1] < 90) or not (-90 < bounds_components[3] < 90):
            logging.error("y out of range %f or %f" % (bounds_components[1], bounds_components[3]))
            return HttpResponseBadRequest("y out of range %f or %f" % (bounds_components[1], bounds_components[3]))

        ll = Point(bounds_components[0], bounds_components[1], srid=4326)
        ll.transform(render_srid)

        ur = Point(bounds_components[2], bounds_components[3], srid=4326)
        ur.transform(render_srid)
        bounds_box = mapnik.Box2d(ll.x, ll.y, ur.x, ur.y)
    elif center:
        center_components = center.split(',')
        if len(center_components) != 3:
            return HttpResponseBadRequest()
        lon = float(center_components[0])
        lat = float(center_components[1])
        zoom = int(center_components[2])
        # todo calc bounds from center and zoom

# baselayer
    if background not in settings.BASE_LAYERS and background != 'none':
        return HttpResponseNotFound("Background not found")

# GeoJSON post data
    if request.method == "POST" and len(request.body):
        input_data = json.loads(request.body)
    else:
        input_data = None

    if not bounds and not center and not input_data:
        return HttpResponseBadRequest("Bounds, center, or post data is required.")

# initialize map
    m = mapnik.Map(width, height)
    m.srs = '+init=epsg:' + str(render_srid)

# add a tile source as a background
    if background != "none":
        background_file = settings.BASE_LAYERS[background]
        background_style = mapnik.Style()
        background_rule = mapnik.Rule()
        background_rule.symbols.append(mapnik.RasterSymbolizer())
        background_style.rules.append(background_rule)
        m.append_style('background style', background_style)
        tile_layer = mapnik.Layer('background')
        tile_layer.srs = '+init=epsg:' + str(render_srid)
        tile_layer.datasource = mapnik.Gdal(base=settings.BASE_LAYER_DIR, file=background_file)
        tile_layer.styles.append('background style')
        m.layers.append(tile_layer)

# add features from geojson
    if input_data and input_data['type'] == "Feature":
        features = [input_data]
    elif input_data and input_data['type'] == "FeatureCollection":
        if 'features' not in input_data:
            return HttpResponseBadRequest()
        features = input_data['features']
    else:
        features = []

    logging.debug("Adding %d features to map" % len(features))

    geometries = []
    point_features = []
    fid = 0
    for feature in features:
        if 'geometry' not in feature:
            logging.debug("feature does not have geometry")
            return HttpResponseBadRequest("Feature does not have a geometry")
        if 'type' not in feature['geometry']:
            logging.debug("geometry does not have type")
            return HttpResponseBadRequest("Geometry does not have a type")

        fid += 1
        style_name = str(fid)

        if feature['geometry']['type'] == 'Point':
            point_features.append(feature)
        elif feature['geometry']['type'] in ('LineString', 'MultiLineString'):
            if feature['geometry']['type'] == 'LineString':
                geos_feature = LineString(feature['geometry']['coordinates'])
            elif feature['geometry']['type'] == 'MultiLineString':
                rings = feature['geometry']['coordinates']
                rings = [[(c[0], c[1]) for c in r] for r in rings]
                if len(rings) == 1:
                    geos_feature = LineString(rings[0])
                else:
                    linestrings = []
                    for ring in rings:
                        try:
                            linestrings.append(LineString(ring))
                        except Exception, e:
                            logging.error("Error adding ring: %s", e)

                    geos_feature = MultiLineString(linestrings)

            geos_feature.srid = 4326
            geos_feature.transform(render_srid)
            geometries.append(geos_feature)

            style = mapnik.Style()
            line_rule = mapnik.Rule()
            style_dict = None
            if 'style' in feature:
                style_dict = feature['style']
            elif 'properties' in feature:
                style_dict = feature['properties']
            line_rule.symbols.append(line_symbolizer(style_dict))
            style.rules.append(line_rule)
            m.append_style(style_name, style)

            wkt = geos_feature.wkt
            line_layer = mapnik.Layer(style_name + ' layer')
            line_layer.datasource = mapnik.CSV(inline='wkt\n' + '"' + wkt + '"')
            line_layer.styles.append(style_name)
            line_layer.srs = '+init=epsg:' + str(render_srid)
            m.layers.append(line_layer)
        elif feature['geometry']['type'] == 'Polygon':
            geos_feature = GEOSGeometry(json.dumps(feature['geometry']))
            geos_feature.srid = 4326
            geos_feature.transform(render_srid)
            geometries.append(geos_feature)

            style = mapnik.Style()
            rule = mapnik.Rule()
            style_dict = None
            if 'style' in feature:
                style_dict = feature['style']
            elif 'properties' in feature:
                style_dict = feature['properties']
            rule.symbols.append(polygon_symbolizer(style_dict))
            rule.symbols.append(line_symbolizer(style_dict))
            style.rules.append(rule)
            m.append_style(style_name, style)

            wkt = geos_feature.wkt
            layer = mapnik.Layer(style_name + ' layer')
            layer.datasource = mapnik.CSV(inline='wkt\n' + '"' + wkt + '"')
            layer.styles.append(style_name)
            layer.srs = '+init=epsg:' + str(render_srid)
            m.layers.append(layer)
        else:
            logging.info("Not adding unknown feature type")

# point features are coaslesced into a single layer for efficiency
    if len(point_features):
        logging.debug("Adding %i point features in 1 layer" % len(point_features))
        point_style = mapnik.Style()
        point_rule = mapnik.Rule()
        point_symbolizer = mapnik.PointSymbolizer()
        point_rule.symbols.append(point_symbolizer)
        point_style.rules.append(point_rule)
        m.append_style('point_style', point_style)

        csv = 'wkt\n'
        for feature in point_features:
            geos_feature = Point(feature['geometry']['coordinates'])
            geos_feature.srid = 4326
            geos_feature.transform(render_srid)
            geometries.append(geos_feature)
            csv += '"' + geos_feature.wkt + '"\n'

        point_layer = mapnik.Layer('point layer')
        point_layer.datasource = mapnik.CSV(inline=csv)
        point_layer.styles.append('point_style')
        point_layer.srs = '+init=epsg:' + str(render_srid)
        m.layers.append(point_layer)

# bounds not in url, calculate from data
    if not bounds_box:
        geometry_collection = GeometryCollection(geometries)
        minx, miny, maxx, maxy = geometry_collection.extent
        buffer_size = .2
        x_buffer_size = ((maxx - minx) * buffer_size)
        y_buffer_size = ((maxy - miny) * buffer_size)
        if x_buffer_size == 0:  # this can happen if there is only 1 point feature
            x_buffer_size = 1000
        if y_buffer_size == 0:
            y_buffer_size = 1000
        bounds_box = mapnik.Box2d(minx - x_buffer_size, miny - y_buffer_size,
                                  maxx + x_buffer_size, maxy + y_buffer_size)

    m.zoom_to_box(bounds_box)

# render image
    im = mapnik.Image(m.width, m.height)
    mapnik.render(m, im)
    data = im.tostring(str(format))

    if background in settings.BASE_LAYERS_ATTRIBUTION:
        image = Image.open(cStringIO.StringIO(data))
        if format.startswith('png'):
            image = image.convert('RGB')  # workaround for Pillow palette bug
        add_attribution(image, settings.BASE_LAYERS_ATTRIBUTION[background])
        output = cStringIO.StringIO()
        match = re.match('^(jpeg|png)(\d{1,3})$', format)
        if match:
            image_format, quality = match.groups()
            quality = int(quality)
            if image_format == 'jpeg':
                image.save(output, 'jpeg', quality=quality)
            else:
                image = image.convert('P', palette=Image.ADAPTIVE, colors=quality)
                bits = int(log(quality, 2))
                image.save(output, 'png', bits=bits)
        else:
            image.save(output, format)
        data = output.getvalue()
        output.close()

    return HttpResponse(data, content_type=mimetype)


def line_symbolizer(style):
    line_symbolizer = mapnik.LineSymbolizer()

    stroke_color = "red"
    stroke_width = 2
    if style:
        if 'stroke' in style:
            stroke_color = str(style['stroke'])
        if 'stroke-width' in style:
            stroke_width = float(style['stroke-width'])

    stroke = mapnik.Stroke(mapnik.Color(stroke_color), stroke_width)
    if style:
        if 'opacity' in style:
            stroke.opacity = float(style['opacity'])
        if 'stroke-dasharray' in style:
            dasharray = [float(d) for d in style['stroke-dasharray']]
            while len(dasharray) >= 2:
                length, gap = dasharray.pop(0), dasharray.pop(0)
                stroke.add_dash(length, gap)
        if 'stroke-linejoin' in style:
            if style['stroke-linejoin'] in LINEJOIN_OPTIONS:
                stroke.linejoin = LINEJOIN_OPTIONS[style['stroke-linejoin']]
            else:
                raise InvalidStyleException()
        if 'stroke-linecap' in style:
            if style['stroke-linecap'] in LINECAP_OPTIONS:
                stroke.linecap = LINECAP_OPTIONS[style['stroke-linecap']]
            else:
                return InvalidStyleException()

    line_symbolizer.stroke = stroke

    if style and 'smooth' in style:
        line_symbolizer.smooth = float(style['smooth'])

    return line_symbolizer


def polygon_symbolizer(style):
    fill_color = "red"
    opacity = 0.6
    if style:
        if 'fill' in style:
            fill_color = str(style['fill'])
        if 'fill-opacity' in style:
            opacity = float(style['fill-opacity'])

    symbolizer = mapnik.PolygonSymbolizer(mapnik.Color(fill_color))
    symbolizer.fill_opacity = opacity

    return symbolizer


def add_attribution(image, text):
    draw = ImageDraw.Draw(image)
    black = (0, 0, 0)
    text_pos = (5, image.size[1] - 12)
    font_path = settings.ATTRIBUTION_FONT
    font = ImageFont.truetype(font_path, settings.ATTRIBUTION_FONT_SIZE)
    draw.text(text_pos, text, fill=black, font=font)
