#!/bin/sh
YEAR=`date +%Y`
MOTHON=`date +%Y%m`
MYDATE=`date +%Y%m%d`
BASEDIR=~/share/zf_history_quantile
BASEDIRSH=~/share/script

FULLDIR=$BASEDIR/$YEAR/$MOTHON
if [ ! -d $FULLDIR ]; then
  mkdir -p $FULLDIR
fi

LOGFILE=$FULLDIR/history_quantile_cron_$MYDATE.log

python $BASEDIRSH/history_quantile.py  >> $LOGFILE