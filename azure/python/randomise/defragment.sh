#!/bin/bash
# fsl randomise defragment script

Usage() {
    echo ""
    echo "Usage: defragment.sh <total iterations> <total tasks> <output prefix>"
    echo "E.g. defragment.sh 5000 10 tbss"
    exit 1
}

if [ "$1" = "" ] || [ "$2" = "" ] || [ "$3" = "" ] ;then
    Usage
fi

for FIRSTSEED in `imglob -extension $3_SEED1_*_p_* $3_SEED1_*_corrp_*` ; do 
  ADDCOMMAND=""
  ACTIVESEED=1
  if [ -e $FIRSTSEED ] ; then
    while [ $ACTIVESEED -le $2 ] ; do
      ADDCOMMAND=`echo $ADDCOMMAND -add ${FIRSTSEED/_SEED1_/_SEED${ACTIVESEED}_}`
      let "ACTIVESEED=ACTIVESEED+1"
    done
    ADDCOMMAND=${ADDCOMMAND#-add}
    #echo $ADDCOMMAND
    fslmaths $ADDCOMMAND -mul `echo "$1/$2"|bc` -div `echo "$1+1-$2"|bc` ${FIRSTSEED/_SEED1/}
  fi
done

echo "Renaming raw stats"
for TYPE in _ _tfce_ ; do
  for FIRSTSEED in `imglob -extension $3_SEED1${TYPE}tstat*` ; do 
    if [ -e $FIRSTSEED ] ; then cp $FIRSTSEED ${FIRSTSEED/_SEED1/}; fi
  done
done

cd ..
