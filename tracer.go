package main

import (
	"crypto/sha256"
	"encoding/base64"
	"fmt"

	pubsub "github.com/libp2p/go-libp2p-pubsub"
	pb "github.com/libp2p/go-libp2p-pubsub/pb"
	"github.com/libp2p/go-libp2p/core/peer"
	"github.com/libp2p/go-libp2p/core/protocol"
	"log"
)

var _ = pubsub.EventTracer(eventTracer{})
var _ = pubsub.RawTracer(gossipTracer{})

type gossipTracer struct{}
type eventTracer struct{}

func (t eventTracer) logRpcEvt(action string, data *pb.TraceEvent_RPCMeta, suffix string) {
	controlData := data.GetControl()

	if len(controlData.GetIhave()) > 0 {
		for _, msg := range controlData.GetIhave() {
			log.Printf("GossipSubRPC: %s IHAVE (topic: %s, ids: %q%s)\n",
				action, msg.GetTopic(), msg.GetMessageIDs(), suffix)
		}
	}
	if len(controlData.GetIwant()) > 0 {
		for _, msg := range controlData.GetIwant() {
			log.Printf("GossipSubRPC: %s IWANT (ids: %q%s)\n",
				action, msg.GetMessageIDs(), suffix)
		}
	}
	if len(controlData.GetIdontwant()) > 0 {
		for _, msg := range controlData.GetIdontwant() {
			log.Printf("GossipSubRPC: %s IDONTWANT (ids: %q%s)\n",
				action, msg.GetMessageIDs(), suffix)
		}
	}
	if len(controlData.GetIannounce()) > 0 {
		for _, msg := range controlData.GetIannounce() {
			log.Printf("GossipSubRPC: %s IANNOUNCE (topic: %s, id: %s%s)\n",
				action, msg.GetTopic(), msg.GetMessageID(), suffix)
		}
	}
	if len(controlData.GetIneed()) > 0 {
		for _, msg := range controlData.GetIneed() {
			log.Printf("GossipSubRPC: %s INEED (id: %s%s)\n",
				action, msg.GetMessageID(), suffix)
		}
	}

	for _, msg := range data.GetMessages() {
		log.Printf("GossipSubRPC: %s Publish (topic: %s, id: %s%s)\n",
			action, msg.GetTopic(), msg.GetMessageID(), suffix)
	}
}

func (t eventTracer) Trace(evt *pb.TraceEvent) {

	if evt.GetType() == pb.TraceEvent_RECV_RPC {
		// we only log control messages here
		from, err := peer.IDFromBytes(evt.GetRecvRPC().GetReceivedFrom())
		if err != nil {
			t.logRpcEvt("Received", evt.GetRecvRPC().GetMeta(), "")
		}
		suffix := fmt.Sprintf(", from: %s", from.String())
		t.logRpcEvt("Received", evt.GetRecvRPC().GetMeta(), suffix)
	} else if evt.GetType() == pb.TraceEvent_SEND_RPC {
		// we only log control messages here
		to, err := peer.IDFromBytes(evt.GetSendRPC().GetSendTo())
		if err != nil {
			t.logRpcEvt("Sent", evt.GetSendRPC().GetMeta(), "")
		}
		suffix := fmt.Sprintf(", to: %s", to.String())
		t.logRpcEvt("Sent", evt.GetSendRPC().GetMeta(), suffix)
	}

}

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
	log.Printf("GossipSub: Validate (id: %s, from: %s)\n", msg.ID, msg.ReceivedFrom.String())
}

// DeliverMessage .
func (g gossipTracer) DeliverMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Delivered (id: %s, from: %s)\n", msg.ID, msg.ReceivedFrom.String())
}

// RejectMessage .
func (g gossipTracer) RejectMessage(msg *pubsub.Message, reason string) {
	log.Printf("GossipSub: Rejected (id: %s, from: %s, reason: %s)\n", msg.ID, msg.ReceivedFrom.String(), reason)
}

// DuplicateMessage .
func (g gossipTracer) DuplicateMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Duplicated (id: %s, from: %s)\n", msg.ID, msg.ReceivedFrom.String())
}

// UndeliverableMessage .
func (g gossipTracer) UndeliverableMessage(msg *pubsub.Message) {
	log.Printf("GossipSub: Undeliverable (id: %s, from: %s)\n", msg.ID, msg.ReceivedFrom.String())
}

// ThrottlePeer .
func (g gossipTracer) ThrottlePeer(p peer.ID) {
	log.Printf("GossipSub: Throttled (peer: %s)\n", p.String())
}

// RecvRPC .
func (g gossipTracer) logRPC(rpc *pubsub.RPC, suffix string, action string) {

	for _, msg := range rpc.Publish {
		log.Printf("GossipSubRPC: %s Publish (topic: %s, id: %s%s)\n",
			action, *msg.Topic, CalcID(msg.Data), suffix)
	}
}

// RecvRPC .
func (g gossipTracer) RecvRPC(rpc *pubsub.RPC) {
}

// SendRPC .
func (g gossipTracer) SendRPC(rpc *pubsub.RPC, p peer.ID) {
}

// DropRPC .
func (g gossipTracer) DropRPC(rpc *pubsub.RPC, p peer.ID) {
	suffix := ", to: " + p.String()
	g.logRPC(rpc, suffix, "Dropped")
}
