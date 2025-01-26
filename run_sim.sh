#!/bin/bash

export SIM_D=8

go build -linkshared

for kb in 128 256 512 1024 2048; do
  for announce in 0 7 8; do
    for num_msgs in 1 2 4 8 16; do
      result=$((kb * 1024))
      filename=shadow-$kb-$announce-$num_msgs
      export SIM_MSG_SIZE=$result
      export SIM_ANNOUNCE=$announce
      export SIM_NUM_MSGS=$num_msgs
      envsubst < shadow.yaml.template > $filename.yaml
      cat $filename.yaml | grep args

      shadow -d $filename.data $filename.yaml

      tar -czvf $filename.tar.gz $filename.data

      rm $filename.yaml
      rm -rf $filename.data
    done
  done
done
