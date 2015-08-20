#!/bin/bash

case "$LOGGING_SYSLOG" in
    "true"|"True"|"yes") /usr/sbin/rsyslogd -n || exit 0;;
esac

# If not running rsyslog, just keep the process going for supervisord
while [ 1 ]; do sleep 60; done
