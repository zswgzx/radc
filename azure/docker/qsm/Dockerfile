FROM ubuntu:18.04

ARG DEBIAN_FRONTEND="noninteractive"

RUN apt-get update -qq \
    && apt-get install -yq --no-install-recommends \
           bc \
           dc \
           libopenblas-dev \
           libxt6 \
           unzip \
           wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && if [ ! -f "/opt/qsm.sh" ]; then \
         echo '#!/usr/bin/env bash' >> /opt/qsm.sh \
    &&   echo 'set -e' >> /opt/qsm.sh \
    &&   echo 'export USER="${USER:=`whoami`}"' >> /opt/qsm.sh;fi \
    && chmod 777 /opt && chmod a+s /opt && chmod a+x /opt/qsm.sh

ENV FSLDIR="/opt/fsl-6.0.3" \
    PATH="/opt/fsl-6.0.3/bin:$PATH"
RUN echo "Downloading FSL ..." \
    && wget --no-check-certificate --progress=bar:force -P /opt https://fsl.fmrib.ox.ac.uk/fsldownloads/fsl-6.0.3-centos6_64.tar.gz \
    && tar xfz /opt/fsl-6.0.3-centos6_64.tar.gz \
    && mv fsl $FSLDIR \
    && rm -rf $FSLDIR/bin/FSLeyes $FSLDIR/data $FSLDIR/lib $FSLDIR/src $FSLDIR/etc/xtract_data \
    && rm -f /opt/fsl-6.0.3-centos6_64.tar.gz $FSLDIR/bin/[a-e]* $FSLDIR/bin/[A-V]* $FSLDIR/bin/[g-z]* $FSLDIR/bin/fsl_* $FSLDIR/bin/fsl[ab]* $FSLDIR/bin/fslc[chor]* $FSLDIR/bin/fsl[d-g]* $FSLDIR/bin/fsli* $FSLDIR/bin/fslm[eo]* $FSLDIR/bin/fsl[nptw]* $FSLDIR/bin/f[a-i]* $FSLDIR/bin/flameo $FSLDIR/bin/fn* $FSLDIR/bin/f[ltu]* $FSLDIR/bin/fsls[ilmtu]* $FSLDIR/bin/fslv[bi]* \
    && echo '. $FSLDIR/etc/fslconf/fsl.sh' >> /opt/qsm.sh

ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/opt/mcr/v95/runtime/glnxa64:/opt/mcr/v95/bin/glnxa64:/opt/mcr/v95/sys/os/glnxa64"
RUN export TMPDIR="$(mktemp -d)" \
    && echo "Downloading MATLAB Compiler Runtime ..." \
    && wget --no-check-certificate --progress=bar:force -P $TMPDIR https://ssd.mathworks.com/supportfiles/downloads/R2018b/deployment_files/R2018b/installers/glnxa64/MCR_R2018b_glnxa64_installer.zip \
    && unzip -q "$TMPDIR/MCR_R2018b_glnxa64_installer.zip" -d "$TMPDIR/mcrtmp" \
    && "$TMPDIR/mcrtmp/install" -destinationFolder /opt/mcr -mode silent -agreeToLicense yes \
    && rm -rf "$TMPDIR" /tmp/mathworks* \
    && unset TMPDIR \
    && mcr_dir="/opt/mcr/v95/bin/glnxa64" \
    && chmod u+w ${mcr_dir} -R \
    && rm -rf ${mcr_dir}/libcublas* ${mcr_dir}/libcudart* ${mcr_dir}/libcudnn* ${mcr_dir}/libcufft* ${mcr_dir}/libcusparse* ${mcr_dir}/libcusolver* ${mcr_dir}/libnccl* ${mcr_dir}/*gpu* ${mcr_dir}/libopencv_cuda* \
    && mcr_dir="/opt/mcr/v95/resource" \
    && rm -rf ${mcr_dir}/aero* ${mcr_dir}/audio ${mcr_dir}/bioinfo ${mcr_dir}/comm ${mcr_dir}/driving ${mcr_dir}/dsp* ${mcr_dir}/econ ${mcr_dir}/fin* ${mcr_dir}/fuzzy ${mcr_dir}/imaq* ${mcr_dir}/instrument ${mcr_dir}/lte ${mcr_dir}/map* ${mcr_dir}/nnet* ${mcr_dir}/pde ${mcr_dir}/phased ${mcr_dir}/predmaint ${mcr_dir}/rf* ${mcr_dir}/risk ${mcr_dir}/robotics ${mcr_dir}/spfres ${mcr_dir}/textanalytics ${mcr_dir}/vision ${mcr_dir}/vnt ${mcr_dir}/wlan /opt/mcr/v95/toolbox/simulink

COPY preproc /usr/local/bin/
COPY postproc /usr/local/bin/
COPY qsm /usr/local/bin/

RUN chmod u+x /usr/local/bin/qsm \
    && chmod u+x /usr/local/bin/preproc \
    && chmod u+x /usr/local/bin/postproc \
    && echo 'qsm $1 /input/$2' >> /opt/qsm.sh \
    && echo 'rm /input/$2/*bet_*;cd /input;tar cfz $2.tgz $2/' >> /opt/qsm.sh

ENTRYPOINT ["/opt/qsm.sh"]
