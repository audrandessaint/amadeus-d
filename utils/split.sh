#!/bin/bash

SORTED_FILE="sortedfile.csv"
OUTPUT_PREFIX="sample"

# Calculate the number of lines per split file
TOTAL_LINES=$(wc -l < $SORTED_FILE)
LINES_PER_FILE=$(echo "($TOTAL_LINES+3)/4" | bc)

# Split the sorted file into 4 parts
split -l $LINES_PER_FILE -d --additional-suffix=.csv $SORTED_FILE ${OUTPUT_PREFIX}

echo "Sorting and splitting done."