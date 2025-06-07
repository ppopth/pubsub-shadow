#!/bin/bash

set -e

go build -linkshared

num_nodes=2000
conns=128
D=8

for num_blobs in 512 256 128 64 32; do
    kbs=$((2 * $num_blobs)) # each cell of the column is 2KB
    for chunk in $kbs 32; do
        column_size=$(($kbs * 1024))
        chunk_size=$(($chunk * 1024))
        filename=shadow-$kbs-chunk-$chunk
        interval=700

        python3 network_graph.py $num_nodes $conns $column_size 128 $D $interval 0 $chunk_size

        shadow --progress true -d $filename.data shadow.yaml

        tar -czf $filename.tar.gz $filename.data

        rm shadow.yaml
        rm -rf $filename.data
    done
done
