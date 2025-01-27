import re
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
                        add_timestamp(msg_id, "rpcs_received", (timestamp, topic))
                    elif "Sent" in log_content:
                        add_timestamp(msg_id, "rpcs_sent", (timestamp, topic))
                elif "IHAVE" in log_content:
                    topic = ext[0]
                    if "Received" in log_content:
                        for msg_id in ext[1]:
                            add_timestamp(msg_id, "ihaves_received", (timestamp, topic))
                    elif "Sent" in log_content:
                        for msg_id in ext[1]:
                            add_timestamp(msg_id, "ihaves_sent", (timestamp, topic))
                elif "IWANT" in log_content:
                    if "Received" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(msg_id, "iwants_received", (timestamp, topic))
                    elif "Sent" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(msg_id, "iwants_sent", (timestamp, topic))
                elif "IDONTWANT" in log_content:
                    if "Received" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(
                                msg_id, "idontwants_received", (timestamp, topic)
                            )
                    elif "Sent" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(msg_id, "idontwants_sent", (timestamp, topic))
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
                        add_timestamp(msg_id, "iannounces_received", (timestamp, topic))
                    elif "Sent" in log_content:
                        add_timestamp(msg_id, "iannounces_sent", (timestamp, topic))
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
    arrival_times = []

    # we know node 0 is the publiisher
    timeline = extracted_data[0]["msgs"]
    publishing_time = -1
    for msg_id in timeline:
        if len(timeline[msg_id]["published"]) > 0:
            # since every messaage is published only once we don't need to sort
            temp_time = (timeline[msg_id]["published"][0])[0]

            # published time is the time at which the first message was published
            if publishing_time < 0 or temp_time < publishing_time:
                publishing_time = temp_time
        else:
            raise Exception("node did not publish")

    for id in extracted_data:
        timeline = extracted_data[id]["msgs"]
        receiving_time = -1
        for msg_id in timeline:
            if len(timeline[msg_id]["delivered"]) > 0:
                # the first time we received a particular msg_id
                temp_time = sorted(timeline[msg_id]["delivered"])[0]
            else:
                temp_time = -1

            # received time is the time at which the last message (any msg_id) was received
            if receiving_time < 0 or temp_time > receiving_time:
                receiving_time = temp_time

        if receiving_time < 0:  # the node for some reason did not receive any messages
            continue  # TODO: there must be implication of this on the plot. Resolve them

        arrival_times.append((id, receiving_time - publishing_time))

    return arrival_times


def plot_cdf(data, label):
    x = [v for _, v in data]
    y = np.arange(len(data)) / float(len(data))

    x.sort()

    plt.plot(x, y, label=label)


if __name__ == "__main__":
    count = int(sys.argv[1])

    timelines = {}
    arr_times = {}

    # read all simulations
    for announce in [0, 7, 8]:
        for msg_size in [128, 256, 512, 1024, 2048]:
            for num_msgs in [1, 2, 4, 8, 16]:
                timeline_key = f"{msg_size}-{announce}-{num_msgs}"
                print(timeline_key)
                timelines[timeline_key] = extract_node_timelines(
                    f"shadow-{timeline_key}.data", count
                )
                arr_times[timeline_key] = analyse_timelines(timelines[timeline_key])

    # 1. plot CDF of arrival times vs. nodes for different message sizes for one msg published
    # three different plots for different Dannounce. Each plot contains 5 CDFs for different sizes
    for announce in [0, 7, 8]:
        plt.figure(figsize=(8, 6))
        for msg_size in [128, 256, 512, 1024, 2048]:
            # only for one message published
            timeline_key = f"{msg_size}-{announce}-1"
            plot_cdf(arr_times[timeline_key], f"{msg_size}KB message")

        plt.xlabel("Message Arrival Time")
        plt.ylabel("Cumulative Proportion of Nodes")
        plt.title(f"Message Arrival Times for D=8 & Dannounce={announce}")
        plt.grid(True)
        plt.legend()
        plt.savefig(f"./plots/cdf_sizes_{announce}.png")

    # 2. plot CDF of arrival times vs. nodes for different numbers of messages(of same size)  published at the same time
    # three different plots for different Dannounce. Each plot contains 5 CDFs for different num of msgs
    for announce in [0, 7, 8]:
        plt.figure(figsize=(8, 6))
        for num_msgs in [1, 2, 4, 8, 16]:
            # only for one message published
            timeline_key = f"{128}-{announce}-{num_msgs}"
            plot_cdf(arr_times[timeline_key], f"{num_msgs} num of msgs")

        plt.xlabel("Message Arrival Time")
        plt.ylabel("Cumulative Proportion of Nodes")
        plt.title(f"Message Arrival Times for D=8 & Dannounce={announce}")
        plt.grid(True)
        plt.legend()
        plt.savefig(f"./plots/cdf_num_{announce}.png")

    # 3. scatter plot of arrival times vs. nodes for different numbers of messages(of same size)  published at the same time
    # three different plots for different Dannounce. Each plot contains 5 CDFs for different num of msgs
    arr_times_merged = [
        (*key.split("-"), value)  # Split the key by "-" and merge it with the value
        for key, values in arr_times.items()
        for value in values
    ]

    latencies = {}
    # reshape by announce values
    for item in arr_times_merged:
        announce_value = item[1]  # The second value of the tuple
        if announce_value not in latencies:
            latencies[announce_value] = []
        latencies[announce_value].append((item[0], item[2], item[3]))

    for announce in latencies:
        latencies_sorted = sorted(latencies[announce], key=lambda x: x[2], reverse=True)

        p95_count = int(len(latencies_sorted) * 0.05)

        p95_latencies = latencies_sorted[:p95_count]

        x_values = [item[0] for item in p95_latencies]
        y_values = [item[1] for item in p95_latencies]

        plt.figure(figsize=(8, 6))
        plt.scatter(x_values, y_values)
        plt.title("Scatter Plot of Msg Size vs Num of Msgs published (later than P95)")
        plt.xlabel("Msg Size in KB")
        plt.ylabel("Number of Messages")
        plt.grid(True)
        plt.savefig(f"./plots/scatter_{announce}.png")
