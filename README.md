# pubsub-shadow

## Requirement

1. A machine with at least 300GB of RAM
2. Have [Shadow](https://shadow.github.io/) installed

## Run the simulations

```bash
bash run_sum.sh
```

## Parse the result and plot the graphs

```bash
for file in shadow-*.tar.gz; do tar xvf $file; done # extract the simulation results
python3 analyse_logs.py 1000
```
