package main

import (
	pubsub "github.com/libp2p/go-libp2p-pubsub"
	"github.com/libp2p/go-libp2p/core/peer"
	"github.com/libp2p/go-libp2p/core/protocol"
	"log"
)

var _ = pubsub.RawTracer(gossipTracer{})

type gossipTracer struct{}

// AddPeer .
func (g gossipTracer) AddPeer(p peer.ID, proto protocol.ID) {
	log.Printf("GossipSub: Peer Added with ID: %s [protocol: %s]\n", p.String(), string(proto))
}

// RemovePeer .
func (g gossipTracer) RemovePeer(p peer.ID) {
	log.Printf("GossipSub: Peer Removed with ID: %s\n", p.String())
}

// Join .
func (g gossipTracer) Join(topic string) {
	log.Printf("GossipSub: Joined topic: %s\n", topic)
}

// Leave .
func (g gossipTracer) Leave(topic string) {
	log.Printf("GossipSub: Left topic: %s\n", topic)
}

// Graft .
func (g gossipTracer) Graft(p peer.ID, topic string) {
	log.Printf("GossipSub: Grafted to %s in topic: %s\n", p.String(), topic)
}

// Prune .
func (g gossipTracer) Prune(p peer.ID, topic string) {
	log.Printf("GossipSub: Pruned to %s in topic: %s\n", p.String(), topic)
}

// ValidateMessage .
func (g gossipTracer) ValidateMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Message entered validation pipeline %s\n", msg.String())
}

// DeliverMessage .
func (g gossipTracer) DeliverMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Delivered message: %s\n", msg.String())
}

// RejectMessage .
func (g gossipTracer) RejectMessage(msg *pubsub.Message, reason string) {
	log.Printf("GossipSub: Rejected message: %s for reason: %s\n", msg.String(), reason)
}

// DuplicateMessage .
func (g gossipTracer) DuplicateMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Duplicate message dropped: %s\n", msg.String())
}

// UndeliverableMessage .
func (g gossipTracer) UndeliverableMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Undeliverable message dropped: %s\n", msg.String())
}

// ThrottlePeer .
func (g gossipTracer) ThrottlePeer(p peer.ID) {
	log.Printf("GossipSub: Peer with id: %s throttled\n", p.String())
}

// RecvRPC .
func (g gossipTracer) RecvRPC(rpc *pubsub.RPC) {
	log.Printf("GossipSub: Received RPC: %s\n", rpc.String())
}

// SendRPC .
func (g gossipTracer) SendRPC(rpc *pubsub.RPC, p peer.ID) {
	log.Printf("GossipSub: Sent RPC: %s to peer: %s\n", rpc.String(), p.String())
}

// DropRPC .
func (g gossipTracer) DropRPC(rpc *pubsub.RPC, p peer.ID) {
	log.Printf("GossipSub: Dropped RPC: %s from peer: %s\n", rpc.String(), p.String())
}
