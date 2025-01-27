#!/bin/bash

for kb in 128 256 512 1024 2048 4096 8192; do
  for announce in 0 7 8; do
    for num in 1 2 4 8 16 32 64; do
      scp -i $1 $2:$3/pubsub-shadow/shadow-$kb-$announce-$num.tar.gz ./shadow-$kb-$announce-$num.tar.gz
      tar -xzf ./shadow-$kb-$announce-$num.tar.gz
    done
  done
done

mkdir -p backup
mv *.tar.gz ./backup/
