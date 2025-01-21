package main

import (
	"context"
	"crypto/ed25519"
	"encoding/binary"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"net"
	"os"
	"time"

	"github.com/libp2p/go-libp2p"
	pubsub "github.com/libp2p/go-libp2p-pubsub"
	"github.com/libp2p/go-libp2p/core/crypto"
	"github.com/libp2p/go-libp2p/core/peer"
)

const (
	topicName = "foobar"
)

var (
	countFlag  = flag.Int("count", 20, "the number of nodes in the network")
	targetFlag = flag.Int("target", 10, "the target number of peers")
)

// compute a private key for node id
func nodePrivKey(id int) crypto.PrivKey {
	seed := make([]byte, ed25519.SeedSize)
	binary.LittleEndian.PutUint64(seed[:8], uint64(id))
	data := ed25519.NewKeyFromSeed(seed)

	privkey, err := crypto.UnmarshalEd25519PrivateKey(data)
	if err != nil {
		panic(err)
	}
	return privkey
}

func main() {
	log.SetOutput(os.Stdout)
	flag.Parse()
	ctx := context.Background()

	hostname, err := os.Hostname()
	if err != nil {
		panic(err)
	}
	log.Printf("Count: %d\n", *countFlag)
	log.Printf("Target: %d\n", *targetFlag)
	log.Printf("Hostname: %s\n", hostname)

	// parse for the node id
	var nodeId int
	if _, err := fmt.Sscanf(hostname, "node%d", &nodeId); err != nil {
		panic(err)
	}
	log.Printf("NodeId: %d\n", nodeId)

	// listen for incoming connections
	h, err := libp2p.New(
		libp2p.ListenAddrStrings("/ip4/0.0.0.0/tcp/9000"),
		libp2p.Identity(nodePrivKey(nodeId)),
	)
	if err != nil {
		panic(err)
	}
	log.Printf("Listening on: %v\n", h.Addrs())

	// wait 1 second for other nodes to bootstrap
	time.Sleep(1 * time.Second)

	// discover peers
	peers := make(map[int]struct{})
	for len(peers) < *targetFlag {
		// do node discovery by picking the node randomly
		id := rand.Intn(*countFlag)
		if _, ok := peers[id]; ok || id == nodeId {
			continue
		}

		// resolve for ip addresses of the discovered node
		addrs, err := net.LookupHost(fmt.Sprintf("node%d", id))
		if err != nil || len(addrs) == 0 {
			log.Printf("Failed resolving for the address of node%d: %v\n", id, err)
			continue
		}

		// craft an addr info to be used to connect
		peerId, err := peer.IDFromPrivateKey(nodePrivKey(id))
		if err != nil {
			panic(err)
		}
		addr := fmt.Sprintf("/ip4/%s/tcp/9000/p2p/%s", addrs[0], peerId)
		info, err := peer.AddrInfoFromString(addr)
		if err != nil {
			panic(err)
		}

		// connect to the peer
		if err = h.Connect(ctx, *info); err != nil {
			log.Printf("Failed connecting to node%d: %v\n", id, err)
			continue
		}
		peers[id] = struct{}{}
		log.Printf("Connected to node%d: %s\n", id, addr)
	}

	// create a gossipsub node and subscribe to the topic
	ps, err := pubsub.NewGossipSub(ctx, h)
	if err != nil {
		panic(err)
	}
	topic, err := ps.Join(topicName)
	if err != nil {
		panic(err)
	}
	sub, err := topic.Subscribe()
	if err != nil {
		panic(err)
	}

	cnt := 0
	for {
		// if it's a turn for the node to publish, publish
		if cnt == nodeId {
			msg := fmt.Sprintf("Hello from node%d", nodeId)
			if err := topic.Publish(ctx, []byte(msg)); err != nil {
				log.Printf("Failed to publish: %s\n", msg)
			} else {
				log.Printf("Published: %s\n", msg)
			}
		}
		// block and wait to receive the next message
		m, err := sub.Next(ctx)
		if err != nil {
			panic(err)
		}
		log.Printf("Received a message from %s: %s", m.ReceivedFrom, string(m.Message.Data))

		cnt++
	}
}
