#!/bin/bash

set -e

go build -linkshared

D=8

for kb in 128 256 512 1024 2048 4096 8192; do
  for announce in 0 $(($D - 1)) $D; do
      result=$((kb * 1024))
      filename=shadow-$kb-$announce-1

      if test $announce -eq 0; then
         interval=700
      else
         interval=1500
      fi

      python3 network_graph.py 1000 35 $result 1 $D $announce $interval 0

      shadow --progress true -d $filename.data shadow.yaml

      tar -czf $filename.tar.gz $filename.data

      rm shadow.yaml
      rm -rf $filename.data
  done
done

for announce in 0 $(($D - 1)) $D; do
  for num_msgs in 2 4 8 16 32 64; do
    result=$((128 * 1024))
    filename=shadow-128-$announce-$num_msgs

    if test $announce -eq 0; then
       interval=700
    else
       interval=1500
    fi
    python3 network_graph.py 1000 35 $result $num_msgs $D $announce $interval 0

    shadow --progress true -d $filename.data shadow.yaml

    tar -czf $filename.tar.gz $filename.data

    rm shadow.yaml
    rm -rf $filename.data
  done
done

for announce in 0 7 8; do
  for malicious in 5 10 20 30 50; do
    result=$((128 * 1024))
    filename=shadow-fault-$fault

    if test $announce -eq 0; then
       interval=700
    else
       interval=1500
    fi
    python3 network_graph.py 1000 35 $result 16 8 $announce $interval $malicious

    shadow --progress true -d $filename.data shadow.yaml

    tar -czf $filename.tar.gz $filename.data

    rm shadow.yaml
    rm -rf $filename.data
  done
done
