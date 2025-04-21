import re
import json
import glob
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
            extracted_data[str(id)] = read_node_logs(logs)

    return extracted_data


def analyse_timelines(extracted_data, shouldhave):
    arrival_times = {}
    rx_msgs = []
    dup_msgs = []

    # we know node 0 is the publiisher
    timeline = extracted_data["0"]["msgs"]

    publishing_times = {}
    first_publish = 0
    last_publish = 0
    for msg_id in timeline:
        if len(timeline[msg_id]["published"]) > 0:
            # since every messaage is published only once we don't need to sort
            publishing_times[msg_id] = (timeline[msg_id]["published"][0])[0]

            if first_publish == 0 or publishing_times[msg_id] < first_publish:
                first_publish = publishing_times[msg_id]

            if publishing_times[msg_id] > last_publish:
                last_publish = publishing_times[msg_id]
        else:
            pass

    for id in extracted_data:
        if id == "0":
            # Skip the publisher node
            continue

        timeline = extracted_data[id]["msgs"]

        dups = 0
        received = 0

        rx_times = {}
        first_receive = 0.0
        last_receive = 0.0
        rx_times_list = []

        for msg_id in timeline:
            if len(timeline[msg_id]["delivered"]) > 0:
                # the first time we received a particular msg_id
                rx_times[msg_id] = sorted(timeline[msg_id]["delivered"])[0]
                rx_times_list.append(rx_times[msg_id])
                # received time is the time at which the last message (any msg_id) was received
                if first_receive == 0.0 or rx_times[msg_id] < first_receive:
                    first_receive = rx_times[msg_id]

                if rx_times[msg_id] > last_receive:
                    last_receive = rx_times[msg_id]

                received += 1

            else:
                rx_times[msg_id] = 0.0

            dups += len(timeline[msg_id]["duplicate"])

            if msg_id not in arrival_times:
                arrival_times[msg_id] = []

            # this can be negative if the message was not received
            arrival_times[msg_id].append(
                (id, rx_times[msg_id] - publishing_times[msg_id])
            )

        if int(id) % 100 == 0:
            print(
                f"Node {id} received {received} messages. Dups: {dups}. Should have received {shouldhave} messages"
            )

        rx_msgs.append(shouldhave - received)
        dup_msgs.append(dups)

        if first_receive == 0.0 or last_receive == 0.0:
            # the node for some reason did not receive any messages
            continue  # TODO: there must be implication of this on the plot. Resolve them

        rx_times_list.sort()
        if first_receive != rx_times_list[0]:
            raise Exception("first_receive != rx_times_list[0]")
        if last_receive != rx_times_list[-1]:
            raise Exception("last_receive != rx_times_list[-1]")

        mid_receive = 20.0
        if len(rx_times_list) >= shouldhave // 2:
            mid_receive = rx_times_list[(shouldhave // 2) - 1]

        if "f2m" not in arrival_times:
            arrival_times["f2m"] = []

        if "f2l" not in arrival_times:
            arrival_times["f2l"] = []

        if "l2f" not in arrival_times:
            arrival_times["l2f"] = []

        arrival_times["f2m"].append((id, mid_receive - first_publish))
        arrival_times["f2l"].append((id, last_receive - first_publish))
        arrival_times["l2f"].append((id, first_receive - last_publish))

    return arrival_times, rx_msgs, dup_msgs


def plot_cdf(data, label):
    x = [v for _, v in data]
    y = np.arange(len(data)) / float(len(data))

    x.sort()

    plt.plot(x, y, label=label)


if __name__ == "__main__":
    count = int(sys.argv[1])
    reparse = True

    timelines = {}
    # this value is tuned after running this script for a couple times
    max_arr_time_size = 20.0
    # this value is tuned after running this script for a couple times
    max_arr_time_num = 20.0

    announce_list = [0, 7, 8]
    size_list = [128, 256, 512, 1024, 2048, 4096, 8192]
    # num_list = [1, 2, 4, 8, 16, 32, 64]
    # num_list = [64, 128]
    num_list = [128]
    malicious_list = [5, 10, 20, 30, 50]

    files = glob.glob("*.tln.json")
    if len(files) > 0:
        print("Found saved timelines")
        for i, file in enumerate(files):
            print(f"{i + 1}. {file}")
        use_saved = input(f"Enter which timeline file to use ({1}-{len(files)}/n):")
        idx = ord(use_saved) - 49
        if idx >= 0 and idx < len(files):
            reparse = False
            with open(files[idx], "r") as f:
                print("Loading timeline file")
                timelines = json.load(f)

    if reparse:
        print("Parsing log files")
        # read all simulations
        # for announce in announce_list:
        #     for msg_size in size_list:
        #         timeline_key = f"{msg_size}-{announce}-1"
        #         print(timeline_key)
        #         timelines[timeline_key] = extract_node_timelines(
        #             f"shadow-{timeline_key}.data", count
        #         )

        # read all simulations
        for announce in announce_list:
            for num_msgs in num_list:
                timeline_key = f"128-{announce}-{num_msgs}"
                print(timeline_key)
                timelines[timeline_key] = extract_node_timelines(
                    f"shadow-{timeline_key}.data", count
                )

        # read all simulations
        # for announce in announce_list:
        #     for malicious in malicious_list:
        #         timeline_key = f"malicious-{malicious}-{announce}"
        #         print(timeline_key)
        #         timelines[timeline_key] = extract_node_timelines(
        #             f"shadow-{timeline_key}.data", count
        #         )

        with open("analysed_timeline.tln.json", "w") as f:
            json.dump(timelines, f)

    # # 1. plot CDF of arrival times vs. nodes for different message sizes for one msg published
    # # three different plots for different Dannounce. Each plot contains 5 CDFs for different sizes
    # for announce in announce_list:
    #     print(f"\nAnnouncement Degree = {announce}\n")
    #     plt.figure(figsize=(8, 6))
    #     for msg_size in size_list:
    #         print(f"\tAnalysis for 1 {msg_size}KB msgs")
    #         # only for one message published
    #         timeline_key = f"{msg_size}-{announce}-1"
    #         arr_times, rx_count, dups = analyse_timelines(timelines[timeline_key], 1)
    #         plot_cdf(arr_times["f2l"], f"{msg_size}KB message")
    #         print(f"\t\tAverage num. of dups: {sum(dups) / count}")
    #         print(f"\t\tAverage num. lost: {sum(rx_count) / count}")

    #     plt.xlabel("Message Arrival Time")
    #     plt.ylabel("Cumulative Proportion of Nodes")
    #     plt.xlim(0.0, max_arr_time_size)
    #     plt.title(f"Message Arrival Times for D=8 & D_announce={announce}")
    #     plt.grid(True)
    #     plt.legend()
    #     plt.savefig(f"./plots/cdf_sizes_{announce}.png")
    #     print("plot saved")

    # 2. plot CDF of arrival times vs. nodes for different numbers of messages(of same size)  published at the same time
    # three different plots for different Dannounce. Each plot contains 5 CDFs for different num of msgs

    def plot_arrival_times(title, num_msgs, arr_times_key):
        print(f"\tAnalysis for {num_msgs} 128KB msgs")
        plt.figure(figsize=(8, 6))
        for announce in announce_list:
            print(f"\nAnnouncement Degree = {announce}\n")
            # only for one message published
            timeline_key = f"{128}-{announce}-{num_msgs}"
            sampling_req = 8  # Nodes should receive 8 messages
            arr_times, rx_count, dups = analyse_timelines(
                timelines[timeline_key], sampling_req
            )
            plot_cdf(arr_times[arr_times_key], f"D_announce={announce}")
            print(f"\t\tAverage num. of dups: {sum(dups) / count}")
            print(f"\t\tAverage num. lost: {sum(rx_count) / count}")

        plt.xlabel("Message Arrival Time")
        plt.ylabel("Cumulative Proportion of Nodes")
        plt.xlim(0.0, max_arr_time_num)
        plt.title(title)
        plt.grid(True)
        plt.legend()
        plt.savefig(f"./plots/cdf_{num_msgs}_msgs__{arr_times_key}.png")
        print("plot saved")

    for num_msgs in num_list:
        plot_arrival_times(
            f"Message Arrival Times for any 4 messages out of 128 messages across 128 topics.\nD=8 and {num_msgs} msgs",
            num_msgs,
            "f2m",
        )
        plot_arrival_times(
            f"Message Arrival Times for the last message received per node out of 128 messages across 128 topics.\nD=8 and {num_msgs} msgs",
            num_msgs,
            "f2l",
        )

    # # 3. plot CDF of arrival times vs. nodes for 16 messages(of same size) published at the same time in presence of malicious nodes
    # # three different plots for different Dannounce. Each plot contains 5 CDFs for different percentages of malicious nodes
    # for announce in announce_list:
    #     print(f"\nAnnouncement Degree = {announce}\n")
    #     plt.figure(figsize=(8, 6))
    #     for malicious in malicious_list:
    #         print(f"\tAnalysis for 16x128KB msgs with {malicious}% malicious nodes")
    #         # only for one message published
    #         timeline_key = f"malicious-{malicious}-{announce}"
    #         arr_times, rx_count, dups = analyse_timelines(
    #             timelines[timeline_key], 16
    #         )
    #         plot_cdf(arr_times["f2l"], f"{malicious}% malicious nodes")
    #         print(f"\t\tAverage num. of dups: {sum(dups) / count}")
    #         print(f"\t\tAverage num. lost: {sum(rx_count) / count}")

    #     plt.xlabel("Message Arrival Time")
    #     plt.ylabel("Cumulative Proportion of Nodes")
    #     plt.xlim(0.0, max_arr_time_num)
    #     plt.title(f"Message Arrival Times for D=8 & D_announce={announce}")
    #     plt.grid(True)
    #     plt.legend()
    #     plt.savefig(f"./plots/cdf_malicious_{announce}.png")
    #     print("plot saved")
