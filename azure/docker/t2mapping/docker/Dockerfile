FROM centos:6

ARG DEBIAN_FRONTEND="noninteractive"

ENV ENTRYPOINT='/opt/t2mapping.sh'
RUN yum install -yq \
      bc \
      ca-certificates \
      gcc \
      libgomp \
      wget \
    && yum clean packages \
    && rm -rf /var/cache/yum/* \
    && if [ ! -f "$ENTRYPOINT" ]; then \
         echo '#!/usr/bin/env bash' >> "$ENTRYPOINT" \
    &&   echo 'set -e' >> "$ENTRYPOINT" \
    &&   echo 'export USER="${USER:=`whoami`}"' >> "$ENTRYPOINT" ;fi \
    && chmod 777 /opt && chmod a+s /opt && chmod +x $ENTRYPOINT

COPY rmFslUnused /usr/bin
ENV FSLDIR='/opt/fsl-6.0.3' \
    PATH="/opt/fsl-6.0.3/bin:$PATH"
RUN echo "Downloading FSL ..." \
    && wget --progress=bar:force -P /opt https://fsl.fmrib.ox.ac.uk/fsldownloads/fsl-6.0.3-centos6_64.tar.gz \
    && cd opt && tar xfz fsl-6.0.3-centos6_64.tar.gz \
    && rm -f fsl-6.0.3-centos6_64.tar.gz && mv fsl fsl-6.0.3 \
    && echo '. $FSLDIR/etc/fslconf/fsl.sh' >> $ENTRYPOINT \
    && rmFslUnused

COPY imtest /opt/fsl-6.0.3/bin/
COPY immv /opt/fsl-6.0.3/bin/
COPY imcp /opt/fsl-6.0.3/bin/
COPY t2_map_mask_float.c /
COPY EstT2PDw /usr/bin

RUN echo "Generating start up script ..." \
    && gcc /t2_map_mask_float.c -o /usr/local/bin/t2_map_mask_float -lm -g -Wall \
    && echo 'time EstT2PDw $1 &> /input/$1.log' >> $ENTRYPOINT

ENTRYPOINT ["/opt/t2mapping.sh"]
