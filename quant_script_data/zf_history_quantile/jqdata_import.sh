#!/bin/sh
YEAR=`date +%Y`
MOTHON=`date +%Y%m`
MYDATE=`date +%Y%m%d`
BASEDIR=~/data_import_sh

FULLDIR=$BASEDIR/$YEAR/$MOTHON
if [ ! -d $FULLDIR ]; then
  mkdir -p $FULLDIR
fi

LOGFILE=$FULLDIR/data_cron_$MYDATE.log

python $BASEDIR/jqdata_manager.py  >> $LOGFILE
