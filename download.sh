#!/bin/bash

for kb in 128 256 512 1024 2048; do
  for announce in 0 7 8; do
    scp -i $1 $2:$3/pubsub-shadow/shadow-$kb-$announce.tar.gz ./shadow-$kb-$announce.tar.gz
    tar -xzvf ./shadow-$kb-$announce.tar.gz
  done
done

mkdir -p backup
mv *.tar.gz ./backup/
