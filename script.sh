#!/bin/bash

# This script is used to run the ENSGrading application.

python grades.py --file "M1_notes.pdf" #-c #Add the -c flag if the transcript you give is certified

python main.py