package main

import (
	"crypto/sha256"
	"encoding/base64"
	"log"

	pubsub "github.com/libp2p/go-libp2p-pubsub"
	"github.com/libp2p/go-libp2p/core/peer"
	"github.com/libp2p/go-libp2p/core/protocol"
)

var _ = pubsub.RawTracer(gossipTracer{})

type gossipTracer struct{}

func CalcID(msg []byte) string {
	hasher := sha256.New()
	hasher.Write(msg)
	return base64.URLEncoding.EncodeToString(hasher.Sum(nil))
}

// AddPeer .
func (g gossipTracer) AddPeer(p peer.ID, proto protocol.ID) {
	log.Printf("GossipSub: Peer Added (id: %s, protocol: %s)\n", p.String(), string(proto))
}

// RemovePeer .
func (g gossipTracer) RemovePeer(p peer.ID) {
	log.Printf("GossipSub: Peer Removed (id: %s)\n", p.String())
}

// Join .
func (g gossipTracer) Join(topic string) {
	log.Printf("GossipSub: Joined (topic: %s)\n", topic)
}

// Leave .
func (g gossipTracer) Leave(topic string) {
	log.Printf("GossipSub: Left (topic: %s)\n", topic)
}

// Graft .
func (g gossipTracer) Graft(p peer.ID, topic string) {
	log.Printf("GossipSub: Grafted (topic: %s, peer: %s)\n", topic, p.String())
}

// Prune .
func (g gossipTracer) Prune(p peer.ID, topic string) {
	log.Printf("GossipSub: Pruned (topic: %s, peer: %s)\n", topic, p.String())
}

// ValidateMessage .
func (g gossipTracer) ValidateMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Validate (id: %s)\n", msg.ID)
}

// DeliverMessage .
func (g gossipTracer) DeliverMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Delivered (id: %s)\n", msg.ID)
}

// RejectMessage .
func (g gossipTracer) RejectMessage(msg *pubsub.Message, reason string) {
	log.Printf("GossipSub: Rejected (id: %s, reason: %s)\n", msg.ID, reason)
}

// DuplicateMessage .
func (g gossipTracer) DuplicateMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Duplicated (id: %s)\n", msg.ID)
}

// UndeliverableMessage .
func (g gossipTracer) UndeliverableMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Undeliverable (id: %s)\n", msg.ID)
}

// ThrottlePeer .
func (g gossipTracer) ThrottlePeer(p peer.ID) {
	log.Printf("GossipSub: Throttled (peer: %s)\n", p.String())
}

// RecvRPC .
func (g gossipTracer) logRPC(rpc *pubsub.RPC, to string, action string) {
	var suffix string = ""
	if len(to) > 0 {
		suffix += ", to: " + to
	}

	if rpc.Control == nil {
		for _, msg := range rpc.Publish {
			log.Printf("GossipSubRPC: %s Publish (topic: %s, id: %s%s)\n",
				action, *msg.Topic, CalcID(msg.Data), suffix)
		}
	} else {
		if len(rpc.Control.Ihave) > 0 {
			for _, msg := range rpc.Control.Ihave {
				log.Printf("GossipSubRPC: %s IHAVE (topic: %s, ids: %q%s)\n",
					action, *msg.TopicID, msg.MessageIDs, suffix)
			}
		} else if len(rpc.Control.Iwant) > 0 {
			for _, msg := range rpc.Control.Iwant {
				log.Printf("GossipSubRPC: %s IWANT (ids: %q%s)\n",
					action, msg.MessageIDs, suffix)
			}
		} else if len(rpc.Control.Idontwant) > 0 {
			for _, msg := range rpc.Control.Idontwant {
				log.Printf("GossipSubRPC: %s IDONTWANT (ids: %q%s)\n",
					action, msg.MessageIDs, suffix)
			}
		} else if len(rpc.Control.Iannounce) > 0 {
			for _, msg := range rpc.Control.Iannounce {
				log.Printf("GossipSubRPC: %s IANNOUNCE (topic: %s, id: %s%s)\n",
					action, *msg.TopicID, *msg.MessageID, suffix)
			}
		} else if len(rpc.Control.Ineed) > 0 {
			for _, msg := range rpc.Control.Ineed {
				log.Printf("GossipSubRPC: %s INEED (id: %s%s)\n",
					action, *msg.MessageID, suffix)
			}
		}
	}

}

// RecvRPC .
func (g gossipTracer) RecvRPC(rpc *pubsub.RPC) {
	g.logRPC(rpc, "", "Received")
}

// SendRPC .
func (g gossipTracer) SendRPC(rpc *pubsub.RPC, p peer.ID) {
	g.logRPC(rpc, p.String(), "Sent")
}

// DropRPC .
func (g gossipTracer) DropRPC(rpc *pubsub.RPC, p peer.ID) {
	g.logRPC(rpc, p.String(), "Dropped")
}
