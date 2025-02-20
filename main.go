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
	pubsubpb "github.com/libp2p/go-libp2p-pubsub/pb"
	"github.com/libp2p/go-libp2p/core/crypto"
	"github.com/libp2p/go-libp2p/core/peer"
)

const (
	topicName = "foobar"
)

var (
	countFlag     = flag.Int("count", 5000, "the number of nodes in the network")
	targetFlag    = flag.Int("target", 70, "the target number of connected peers")
	DFlag         = flag.Int("D", 8, "mesh degree for gossipsub topics")
	DannounceFlag = flag.Int("Dannounce", 8, "announcesub degree for gossipsub topics")
	msgSizeFlag   = flag.Int("size", 32, "message size in bytes")
	numMsgsFlag   = flag.Int("n", 1, "number of messages published at the same time")
)

// creates a custom gossipsub parameter set.
func pubsubGossipParam() pubsub.GossipSubParams {
	gParams := pubsub.DefaultGossipSubParams()
	gParams.Dlo = 6
	gParams.D = *DFlag
	gParams.Dhi = 12
	gParams.HeartbeatInterval = 700 * time.Millisecond
	gParams.HistoryLength = 6
	gParams.HistoryGossip = 3
	gParams.Dannounce = *DannounceFlag
	return gParams
}

// pubsubOptions creates a list of options to configure our router with.
func pubsubOptions() []pubsub.Option {
	psOpts := []pubsub.Option{
		pubsub.WithMessageSignaturePolicy(pubsub.StrictNoSign),
		pubsub.WithNoAuthor(),
		pubsub.WithMessageIdFn(func(pmsg *pubsubpb.Message) string {
			return CalcID(pmsg.Data)
		}),
		pubsub.WithPeerOutboundQueueSize(600),
		pubsub.WithMaxMessageSize(10 * 1 << 20),
		pubsub.WithValidateQueueSize(600),
		pubsub.WithGossipSubParams(pubsubGossipParam()),
		pubsub.WithRawTracer(gossipTracer{}),
		pubsub.WithEventTracer(eventTracer{}),
	}

	return psOpts
}

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
	log.SetFlags(log.LstdFlags | log.Lmicroseconds)

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
	log.Printf("PeerId: %s\n", h.ID())
	log.Printf("Listening on: %v\n", h.Addrs())

	// create a gossipsub node and subscribe to the topic
	psOpts := pubsubOptions()
	ps, err := pubsub.NewGossipSub(ctx, h, psOpts...)
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

	// wait 30 seconds for other nodes to bootstrap
	time.Sleep(30 * time.Second)

	// discover peers
	peers := make(map[int]struct{})
	for len(h.Network().Peers()) < *targetFlag {
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

	// wait sometime until all meshes are fomed
	time.Sleep(1 * time.Minute)

	// if it's a turn for the node to publish, publish
	if nodeId == 0 {
		for i := 0; i < *numMsgsFlag; i++ {
			msg := make([]byte, *msgSizeFlag)
			rand.Read(msg) // it takes about a 50-100 us to fill the buffer on macpro 2019. Can be considered simulataneous
			if err := topic.Publish(ctx, msg); err != nil {
				log.Printf("Failed to publish message by %s\n", h.ID())
			} else {
				log.Printf("Published: (topic: %s, id: %s)\n", topicName, CalcID(msg))
			}
		}
	}

	for {
		// block and wait to receive the next message
		m, err := sub.Next(ctx)
		if err != nil {
			panic(err)
		}
		log.Printf("Received: (topic: %s, id: %s)\n", *m.Topic, CalcID(m.Message.Data))
	}

}
