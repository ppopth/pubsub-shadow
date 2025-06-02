#!/bin/bash

set -e

go build -linkshared

num_nodes=2000
conns=128
D=8

for num_blobs in 64 32; do
  for announce in 0 $(($D - 1)) $D; do
    kbs=$((2 * $num_blobs)) # each cell of the column is 2KB
    result=$(($kbs * 1024))
    filename=shadow-$kbs-$announce-128

    if test $announce -eq 0; then
       interval=700
    else
       interval=1500
    fi
    python3 network_graph.py $num_nodes $conns $result 128 $D $announce $interval 0

    shadow --progress true -d $filename.data shadow.yaml

    tar -czf $filename.tar.gz $filename.data

    rm shadow.yaml
    rm -rf $filename.data
  done
done
