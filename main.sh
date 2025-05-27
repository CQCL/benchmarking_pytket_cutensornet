#!/bin/bash

# Clean up
rm -r tmp/
mkdir tmp/

# Generate the input parameters for the script.sh files
# Gather them in groups of four so that each run node runs
# four simulations, assigning each one to one of the four GPUs.
i=0
j=0
for dir in ./settings/*/; do
  while read -r filename; do
    if [ $i = 0 ]; then
        touch tmp/input_$j.txt
    fi
    echo "$i $dir $filename" >> tmp/input_$j.txt
    ((i++))
    if [ $i = 4 ]; then
        i=0
        ((j++))
    fi
  done < $dir"circuits.txt"
done

# Issue the jobs
for inputfile in tmp/*; do
  sbatch script.sh $inputfile
done
