# pubsub-shadow

## Build

Build the implementation to be simulated.
```bash
go build -linkshared
```

Given the number of nodes, generate a Shadow config file and a network graph, named as `shadow.yaml` and `graph.gml` respectively.
```bash
# python3 network_graph.py [NODE_COUNT] [NUM_CONNECTIONS] [MSG_SIZE_IN_BYTES] [NUM_MSGS_PUBLISHED] [MESH_DEGREE] {ANNOUNCE_DEGREE]
python network_graph.py 100 10 32 1 8 7
```
The number of nodes shown is 100. Change it correspondingly.

## Run the simulation


### Manual
Remove the old simulation result first.
```bash
rm -rf shadow.data
```

Run the simulation.
```bash
shadow --progress true shadow.yaml
```
