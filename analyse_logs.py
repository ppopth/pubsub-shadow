import re
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Define the updated regex pattern
line_pattern = r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{6})\s+(.*)"

BASE_PATH = "./shadow.data/hosts/node"
STDOUT_LOGFILE = "/pubsub-shadow.1000.stdout"

# Open the file and read it line by line


def read_node_logs(id):
    timeline = {
        "connected": [],
        "disconnected": [],
        "added": [],
        "removed": [],
        "throttled": [],
        "joined": [],
        "left": [],
        "grafted": [],
        "pruned": [],
        "validated": [],
        "delivered": [],
        "rejected": [],
        "received": [],
        "published": [],
        "duplicate": [],
        "undelivered": [],
    }

    with open(
        BASE_PATH + str(id) + STDOUT_LOGFILE, "r", encoding="utf-8", errors="replace"
    ) as f:
        for line in f:
            match = re.match(line_pattern, line.strip())
            if match:
                log_date_time = match.group(1)  # Date (YYYY/MM/DD)
                log_content = match.group(2)  # Log content

                timestamp = datetime.strptime(
                    log_date_time, "%Y/%m/%d %H:%M:%S.%f"
                ).timestamp()

                if "Duplicate message dropped" in log_content:
                    msg_id = 0  # TODO: extract msg id
                    timeline["duplicate"].append((timestamp, msg_id))
                elif "Received a message from" in log_content:
                    msg_id = 0  # TODO: extract msg id
                    timeline["received"].append((timestamp, msg_id))
                elif "Published message by" in log_content:
                    msg_id = 0  # TODO: extract msg id
                    timeline["published"].append((timestamp, msg_id))
                elif "Rejected" in log_content:
                    msg_id = 0  # TODO: extract msg id
                    timeline["rejected"].append((timestamp, msg_id))
                elif "Delivered" in log_content:
                    msg_id = 0  # TODO: extract msg id
                    timeline["delivered"].append((timestamp, msg_id))
                elif "Grafted to":
                    topic = ""  # TODO: extract topic
                    timeline["grafted"].append((timestamp, topic))
                elif "Pruned to":
                    topic = ""  # TODO: extract topic
                    timeline["pruned"].append((timestamp, topic))
                elif "Joined topic":
                    topic = ""  # TODO: extract topic
                    timeline["joined"].append((timestamp, topic))
                elif "Left topic":
                    topic = ""  # TODO: extract topic
                    timeline["left"].append((timestamp, topic))
                elif "Peer removed":
                    peer_id = ""  # TODO: extract peer id
                    timeline["removed"].append((timestamp, peer_id))
                elif "Peer added":
                    peer_id = ""  # TODO: extract peer id
                    timeline["added"].append((timestamp, peer_id))
                elif "Undeliverable message dropped":
                    msg_id = 0  # TODO: extract msg id
                    timeline["undelivered"].append((timestamp, msg_id))
                elif "throttled":
                    peer_id = ""  # TODO: extract peer id
                    timeline["thottled"].append((timestamp, peer_id))
            else:
                raise Exception(
                    'Couldn\'t match pattern for "Received Message"')
    return timeline


def analyse_logs(count):
    extracted_data = {}
    sum = 0
    published_time = 0

    for id in range(count):
        timeline = read_node_logs(id)
        sum += len(timeline["duplicate"])

        if len(timeline["published"]) > 0:
            published_time = (timeline["published"][0])[0]

        extracted_data[id] = timeline

    avg_dups = sum / count

    arrival_times = []
    for id in extracted_data:
        if len(extracted_data[id]["delivered"]) > 0:
            recv_time = (sorted(extracted_data[id]["delivered"])[0])[0]
            arrival_times.append((id, recv_time - published_time))

    return arrival_times, avg_dups


def plot_cdf(data, label):
    x = [v for _, v in data]
    y = np.arange(len(data)) / float(len(data))

    x.sort()

    plt.figure(figsize=(8, 6))
    plt.plot(x, y, label=label)
    plt.xlabel("Message Arrival Time")
    plt.ylabel("Cumulative Proportion of Nodes")
    plt.title("CDF of Message Arrival Times")
    plt.grid(True)
    plt.legend()
    plt.savefig("./plots/cdf_arrival_times.png")


if __name__ == "__main__":
    arr_times, dups = analyse_logs(100)
    print(f"Average number of duplicates: {dups}")

    plot_cdf(arr_times, "size 128 bytes")
