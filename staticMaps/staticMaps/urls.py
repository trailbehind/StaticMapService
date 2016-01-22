from django.conf.urls import patterns, include, url
from django.contrib import admin
from views import status as status_view

urlpatterns = patterns('',
    url(r'^status/$', status_view),
	url(r'^', include('mapRender.urls'))
)
