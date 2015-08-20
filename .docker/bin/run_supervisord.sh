#!/bin/bash

# Runs supervisord, tailing any logfiles

set -eu

LOGS=/var/log
CONF_FILE=/opt/supervisor/$1.conf
LOGGING_SYSLOG=${LOGGING_SYSLOG:-""}

case "$LOGGING_SYSLOG" in
    "true"|"True"|"yes") echo "
\*.\*          @@$LOGSERVER
" >> /etc/rsyslog.conf
    ;;
*)
    echo "*.*    ${LOGS}/syslog.log" >> /etc/rsyslog.conf
    (umask 0 && truncate -s0 ${LOGS}/syslog.log)
    tail -q --pid $$ -n0 -F $LOGS/syslog.log &
    ;;
esac

exec /usr/bin/supervisord -c $CONF_FILE -n
