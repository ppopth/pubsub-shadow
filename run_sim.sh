#!/bin/bash

go build -linkshared

for kb in 128 256 512 1024 2048 4096; do
  for announce in 0 7 8; do
    for num_msgs in 1 2 4 8 16 32 64; do
      result=$((kb * 1024))
      filename=shadow-$kb-$announce-$num_msgs
      python3 network_graph.py 100 70 $result $num_msgs 8 $announce

      shadow -d $filename.data shadow.yaml

      tar -czf $filename.tar.gz $filename.data

      rm shadow.yaml
      rm -rf $filename.data
    done
  done
done
