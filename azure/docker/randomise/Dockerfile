FROM ubuntu:18.04

ARG DEBIAN_FRONTEND="noninteractive"

RUN apt-get update -qq \
    && apt-get install -yq --no-install-recommends \
           bc \
           dc \
           libgomp1 \
           wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && if [ ! -f "/opt/randomise.sh" ]; then \
         echo '#!/usr/bin/env bash' >> /opt/randomise.sh \
    &&   echo 'set -e' >> /opt/randomise.sh \
    &&   echo 'export USER="${USER:=`whoami`}"' >> /opt/randomise.sh;fi \
    && chmod 777 /opt && chmod a+s /opt && chmod a+x /opt/randomise.sh

ENV FSLDIR="/opt/fsl-6.0.3" \
    PATH="/opt/fsl-6.0.3/bin:$PATH"
RUN wget --no-check-certificate --progress=bar:force -P /opt https://fsl.fmrib.ox.ac.uk/fsldownloads/fsl-6.0.3-centos6_64.tar.gz \
    && cd opt && tar xfz fsl-6.0.3-centos6_64.tar.gz \
    && rm fsl-6.0.3-centos6_64.tar.gz && mv fsl fsl-6.0.3 \
    && echo '. $FSLDIR/etc/fslconf/fsl.sh' >> /opt/randomise.sh \
    && echo "Clean up unused FSL components ..." \
    && rm -r $FSLDIR/bin/fsl $FSLDIR/data $FSLDIR/lib $FSLDIR/src $FSLDIR/etc/xtract_data $FSLDIR/doc \
    && rm $FSLDIR/bin/[a-e]* $FSLDIR/bin/[A-V]* $FSLDIR/bin/[f-q]* $FSLDIR/bin/r[emou]* $FSLDIR/bin/[s-z]*

COPY randomise_openmp $FSLDIR/bin/

RUN echo "Generating start up script ..." \
    && echo 'cd /input;seednum=$1' >> /opt/randomise.sh \
    && echo 'randomise_openmp --uncorrp -T -D -m Tmin-mask -d design.mat -t design.con -e design.grp -i all-t2s --seed=$seednum -n 100 -o t2-SEED$seednum' >> /opt/randomise.sh

ENTRYPOINT ["/opt/randomise.sh"]
