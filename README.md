# pubsub-shadow

## Build

Build the implementation to be simulated.
```bash
go build -linkshared
```

Given the number of nodes, generate a Shadow config file and a network graph, named as `shadow.yaml` and `graph.gml` respectively.
```bash
python network_graph.py 100
```
The number of nodes shown is 100. Change it correspondingly.

## Run the simulation

Remove the old simulation result first.
```bash
rm -rf shadow.data
```

Run the simulation.
```bash
shadow --progress true shadow.yaml
```
