from django.conf.urls import *
import views

urlpatterns = patterns('',
    (r'^(?P<bounds>-?\d{1,3}\.?\d*,-?\d{1,2}\.?\d*,-?\d{1,3}\.?\d*,-?\d{1,2}\.?\d*)/(?P<width>\d+)x(?P<height>\d+)/(?P<background>[a-z]+).(?P<format>[a-z0-9]+)',
     views.render_static),
    (r'^(?P<width>\d+)x(?P<height>\d+)/(?P<background>[a-z]+).(?P<format>[a-z0-9]+)',
     views.render_static),
)
