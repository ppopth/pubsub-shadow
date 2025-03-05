#!/bin/bash

set -e

go build -linkshared

for kb in 128 256 512 1024 2048 4096 8192; do
  for announce in 0 7 8; do
      result=$((kb * 1024))
      filename=shadow-$kb-$announce-1
      python3 network_graph.py 5000 35 $result 1 8 $announce 0

      shadow --progress true -d $filename.data shadow.yaml

      tar -czf $filename.tar.gz $filename.data

      rm shadow.yaml
      rm -rf $filename.data
  done
done

for announce in 0 7 8; do
  for num_msgs in 2 4 8 16 32 64; do
    result=$((128 * 1024))
    filename=shadow-128-$announce-$num_msgs
    python3 network_graph.py 5000 35 $result $num_msgs 8 $announce 0

    shadow --progress true -d $filename.data shadow.yaml

    tar -czf $filename.tar.gz $filename.data

    rm shadow.yaml
    rm -rf $filename.data
  done
done

for announce in 0 7 8; do
  for fault in 5 10 20 30 50; do
    result=$((128 * 1024))
    filename=shadow-fault-$fault
    python3 network_graph.py 5000 35 $result 16 8 $announce $fault

    shadow --progress true -d $filename.data shadow.yaml

    tar -czf $filename.tar.gz $filename.data

    rm shadow.yaml
    rm -rf $filename.data
  done
done
