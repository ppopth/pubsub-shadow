package main

import (
	"flag"
	"fmt"
	"os"
)

var (
	countFlag = flag.Int("count", 20, "the number of nodes in the network")
)

func main() {
	flag.Parse()
	hostname, err := os.Hostname()
	if err != nil {
		panic(err)
	}
	fmt.Printf("Hostname: %s\n", hostname)
	fmt.Printf("Count: %d\n", *countFlag)
}
