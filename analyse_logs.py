import re
import copy
import sys
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Define the updated regex pattern
line_pattern = r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{6})\s+(.*)"
paranthesis_pattern = r"\((.*?)\)"

BASE_PATH = "/hosts/node"
STDOUT_LOGFILE = "/pubsub-shadow.1000.stdout"


def extract_data(log_line):
    info_match = re.search(paranthesis_pattern, log_line)
    values = []
    if info_match:
        pairs = (info_match.group(1)).split(", ")
        for item in pairs:
            value = item.split(": ")[1]
            if "[" in value:
                matches = re.findall(r'"([^"]+)"', value)
                values.append(matches)
            else:
                values.append(value)
    else:
        raise Exception("couldn't extract content for log_line" + log_line)

    return values


def read_node_logs(lines):
    timelines = {
        "added": [],
        "removed": [],
        "throttled": [],
        "joined": [],
        "left": [],
        "grafted": [],
        "pruned": [],
        "msgs": {},
    }

    def add_timestamp(msg_id, key, timestamp):
        if msg_id is None:
            timelines[key].append(timestamp)
            return

        msg_id = msg_id.replace('"', "")

        if msg_id not in timelines["msgs"]:
            timelines["msgs"][msg_id] = {
                "validated": [],
                "delivered": [],
                "rejected": [],
                "received": [],
                "published": [],
                "duplicate": [],
                "undelivered": [],
                "idontwants_sent": [],
                "idontwants_received": [],
                "ihaves_sent": [],
                "ihaves_received": [],
                "iwants_sent": [],
                "iwants_received": [],
                "iannounces_sent": [],
                "iannounces_received": [],
                "ineeds_sent": [],
                "ineeds_received": [],
                # these are publish messages of the rpc
                "rpcs_sent": [],
                "rpcs_received": [],
            }

        timelines["msgs"][msg_id][key].append(timestamp)

    for line in lines:
        match = re.match(line_pattern, line.strip())
        if match:
            log_date_time = match.group(1)  # Date (YYYY/MM/DD)
            log_content = match.group(2)  # Log content

            timestamp = datetime.strptime(
                log_date_time, "%Y/%m/%d %H:%M:%S.%f"
            ).timestamp()

            if "GossipSub: Duplicated" in log_content:
                ext = extract_data(log_content)
                msg_id = ext[0]
                add_timestamp(msg_id, "duplicate", (timestamp))
            elif "Received:" in log_content:
                ext = extract_data(log_content)
                msg_id = ext[1]
                topic = ext[0]
                add_timestamp(msg_id, "received", (timestamp, topic))
            elif "Published:" in log_content:
                ext = extract_data(log_content)
                msg_id = ext[1]
                topic = ext[0]
                add_timestamp(msg_id, "published", (timestamp, topic))
            elif "GossipSub: Rejected" in log_content:
                ext = extract_data(log_content)
                msg_id = ext[0]
                add_timestamp(msg_id, "rejected", (timestamp))
            elif "GossipSub: Delivered" in log_content:
                ext = extract_data(log_content)
                msg_id = ext[0]
                add_timestamp(msg_id, "delivered", (timestamp))
            elif "GossipSub: Undeliverable" in log_content:
                ext = extract_data(log_content)
                msg_id = ext[0]
                add_timestamp(msg_id, "undelivered", (timestamp))
            elif "GossipSub: Validated" in log_content:
                ext = extract_data(log_content)
                msg_id = ext[0]
                add_timestamp(msg_id, "validated", (timestamp))
            elif "GossipSub: Grafted" in log_content:
                ext = extract_data(log_content)
                peer_id = ext[1]
                topic = ext[0]
                add_timestamp(None, "grafted", (timestamp, topic, peer_id))
            elif "GossipSub: Pruned" in log_content:
                ext = extract_data(log_content)
                peer_id = ext[1]
                topic = ext[0]
                add_timestamp(None, "pruned", (timestamp, topic, peer_id))
            elif "GossipSub: Joined" in log_content:
                ext = extract_data(log_content)
                topic = ext[0]
                add_timestamp(None, "joined", (timestamp, topic))
            elif "GossipSub: Left" in log_content:
                ext = extract_data(log_content)
                topic = ext[0]
                add_timestamp(None, "left", (timestamp, topic))
            elif "GossipSub: Peer Removed" in log_content:
                ext = extract_data(log_content)
                peer_id = ext[0]
                add_timestamp(None, "removed", (timestamp, peer_id))
            elif "GossipSub: Peer Added" in log_content:
                ext = extract_data(log_content)
                peer_id = ext[0]
                add_timestamp(None, "added", (timestamp, topic))
            elif "GossipSub: Throttled" in log_content:
                ext = extract_data(log_content)
                peer_id = ext[0]
                add_timestamp(None, "throttled", (timestamp, peer_id))
            elif "GossipSubRPC:" in log_content:
                ext = extract_data(log_content)
                if "Publish" in log_content:
                    msg_id = ext[1]
                    topic = ext[0]
                    if "Received" in log_content:
                        add_timestamp(msg_id, "rpcs_received",
                                      (timestamp, topic))
                    elif "Sent" in log_content:
                        add_timestamp(msg_id, "rpcs_sent", (timestamp, topic))
                elif "IHAVE" in log_content:
                    topic = ext[0]
                    if "Received" in log_content:
                        for msg_id in ext[1]:
                            add_timestamp(
                                msg_id, "ihaves_received", (timestamp, topic))
                    elif "Sent" in log_content:
                        for msg_id in ext[1]:
                            add_timestamp(msg_id, "ihaves_sent",
                                          (timestamp, topic))
                elif "IWANT" in log_content:
                    if "Received" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(
                                msg_id, "iwants_received", (timestamp, topic))
                    elif "Sent" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(msg_id, "iwants_sent",
                                          (timestamp, topic))
                elif "IDONTWANT" in log_content:
                    if "Received" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(
                                msg_id, "idontwants_received", (
                                    timestamp, topic)
                            )
                    elif "Sent" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(
                                msg_id, "idontwants_sent", (timestamp, topic))
                elif "INEED" in log_content:
                    msg_id = ext[0]
                    if "Received" in log_content:
                        add_timestamp(msg_id, "ineeds_received", (timestamp))
                    elif "Sent" in log_content:
                        add_timestamp(msg_id, "ineeds_sent", (timestamp))
                elif "IANNOUNCE" in log_content:
                    msg_id = ext[1]
                    topic = ext[0]
                    if "Received" in log_content:
                        add_timestamp(
                            msg_id, "iannounces_received", (timestamp, topic))
                    elif "Sent" in log_content:
                        add_timestamp(msg_id, "iannounces_sent",
                                      (timestamp, topic))
        else:
            raise Exception("Couldn't match pattern for timestamps")

    return timelines


def extract_node_timelines(folder, count):
    extracted_data = {}
    for id in range(count):
        with open(
            folder + BASE_PATH + str(id) + STDOUT_LOGFILE,
            "r",
            encoding="utf-8",
            errors="replace",
        ) as f:
            logs = f.readlines()
            extracted_data[id] = read_node_logs(logs)

    return extracted_data


def analyse_timelines(extracted_data):
    published_time = {}
    dups = {}
    arrival_times = {}

    for id in extracted_data:
        timeline = extracted_data[id]["msgs"]
        for msg_id in timeline:
            if msg_id not in dups:
                dups[msg_id] = []
                published_time[msg_id] = 0
            dups[msg_id].append(len(timeline[msg_id]["duplicate"]))

            if len(timeline[msg_id]["published"]) > 0:
                published_time[msg_id] = (timeline[msg_id]["published"][0])[0]

    for id in extracted_data:
        timeline = extracted_data[id]["msgs"]
        for msg_id in timeline:
            if msg_id not in arrival_times:
                arrival_times[msg_id] = []

            if len(timeline[msg_id]["delivered"]) > 0:
                recv_time = sorted(timeline[msg_id]["delivered"])[0]
                arrival_times[msg_id].append(
                    (id, recv_time - published_time[msg_id]))

    return arrival_times, dups


def plot_cdf(data, label):
    x = [v for _, v in data]
    y = np.arange(len(data)) / float(len(data))

    x.sort()

    plt.plot(x, y, label=label)
    plt.xlabel("Message Arrival Time")
    plt.ylabel("Cumulative Proportion of Nodes")


if __name__ == "__main__":
    count = int(sys.argv[1])

    timelines = {}

    for announce in [0, 7, 8]:
        if announce not in timelines:
            timelines[announce] = {}
        plt.figure(figsize=(8, 6))
        for msg_size in [128, 256, 512, 1024, 2048]:
            print(f"Processing for Dannounce: {
                  announce} and {msg_size}KB msg size")
            timelines[announce][msg_size] = extract_node_timelines(
                f"shadow-{msg_size}-{announce}.data", count
            )
            arr_times, dups = analyse_timelines(timelines[announce][msg_size])

            for msg_id in arr_times:
                print(
                    f"Average number of duplicates: {
                        np.sum(dups[msg_id])/count}"
                )
                print(f"Median number of duplicates: {
                      np.median(dups[msg_id])}")
                plot_cdf(arr_times[msg_id], f"{msg_size}KB message")

        plt.title(f"Message Arrival Times for D=8 & Dannounce={announce}")
        plt.grid(True)
        plt.legend()
        plt.savefig(f"./plots/cdf_arrival_times_{announce}.png")
