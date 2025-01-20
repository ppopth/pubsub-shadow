# pubsub-shadow

## Build

```bash
go build -linkshared
```

## Run the simulation

Remove the old simulation result first
```bash
rm -rf shadow.data
```

Run the simulation
```bash
shadow shadow.yaml
```
