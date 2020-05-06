#!/usr/bin/env python
'''xnat container command to docker file label
Usage: command2label <command>...
e.g., python command2label.py command.json >> Dockerfile 
'''
# https://wiki.xnat.org/container-service/command-31785434.html

import re
import sys
import json

argsList = sys.argv[1:]

commandStrList = []
for commandFile in argsList:
    with open(commandFile) as f:
        commandObj = json.load(f)
    commandStr = json.dumps(commandObj) \
                        .replace('"', r'\"') \
                        .replace('$', r'\$')
    commandStrList.append(commandStr)

print('LABEL org.nrg.commands="[{}]"'.format(', \\\n\t'.join(commandStrList)))
