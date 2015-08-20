#!/bin/bash

[ $SHLVL = 2 ] && echo "Usage: . ${0##*/}" && exit

if [ ! -d ~/python/staticMaps ]
	then
		test -e ~/python || mkdir ~/python
		pushd .
		cd ~/python
		virtualenv staticMaps
		popd
fi

source ~/python/staticMaps/bin/activate

export PYTHONPATH=~/python/staticMaps/lib/python2.7/site-packages

pip install -r staticMaps/requirements.txt

export PYTHONPATH=~/python/staticMaps/lib/python2.7/site-packages:/usr/local/lib/python2.7/site-packages
