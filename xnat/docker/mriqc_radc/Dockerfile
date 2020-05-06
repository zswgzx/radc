FROM poldracklab/mriqc:latest

COPY dataset_description.json /bidsformat/
COPY setup_bids.sh /bidsformatrun/
RUN ["chmod","777","/bidsformatrun/setup_bids.sh"]
RUN ["chmod","-R","777","/bidsformat"]

ENTRYPOINT /bidsformatrun/setup_bids.sh

LABEL org.nrg.commands="[{\"name\": \"mriqcT1w\", \"label\": \"mriqcT1w\", \"description\": \"Runs invivo T1w mriqc (v0.15.0)\", \"version\": \"1\", \"schema-version\": \"1.0\", \"info-url\": \"https://mriqc.readthedocs.io/en/stable/\", \"image\": \"zswgzx/mriqc_radc:latest\", \"type\": \"docker\", \"command-line\": \"\", \"mounts\": [{\"name\": \"data-in\", \"writable\": false, \"path\": \"/data\"}, {\"name\": \"data-out\", \"writable\": true, \"path\": \"/out\"}], \"inputs\": [], \"outputs\": [{\"name\": \"mriqc\", \"description\": \"mriqc outputs\", \"required\": true, \"mount\": \"data-out\"}], \"xnat\": [{\"name\": \"mriqcT1w-session\", \"label\": \"mriqcT1w\", \"description\": \"Runs invivo T1w mriqc (v0.15.0) on a Session\", \"contexts\": [\"xnat:imageSessionData\"], \"external-inputs\": [{\"name\": \"session\", \"description\": \"Input session\", \"type\": \"Session\", \"required\": true}], \"derived-inputs\": [{\"name\": \"scan\", \"description\": \"Input scan from session\", \"type\": \"Scan\", \"matcher\": \"@.scan-type == 'MPRAGE'\", \"required\": true, \"load-children\": true, \"derived-from-wrapper-input\": \"session\", \"derived-from-xnat-object-property\": \"Scan\"}, {\"name\": \"scan-nifti\", \"description\": \"The nifti resource on the scan\", \"type\": \"Resource\", \"matcher\": \"@.label == 'NIFTI'\", \"required\": true, \"provides-files-for-command-mount\": \"data-in\", \"load-children\": true, \"derived-from-wrapper-input\": \"scan\"}], \"output-handlers\": [{\"name\": \"mriqc-resource\", \"type\": \"Resource\", \"accepts-command-output\": \"mriqc\", \"as-a-child-of\": \"session\", \"label\": \"MRIQC\"}]}]}]"
