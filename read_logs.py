import re
import h5py
import sys
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def read_node_logs(folder, id):
    with open(
        folder + BASE_PATH + str(id) + STDOUT_LOGFILE,
        "r",
        encoding="utf-8",
        errors="replace",
    ) as f:
        lines = f.readlines()

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
                # add_timestamp(msg_id, "received", (timestamp, topic))
                add_timestamp(msg_id, "received", (timestamp))
            elif "Published:" in log_content:
                ext = extract_data(log_content)
                msg_id = ext[1]
                topic = ext[0]
                # add_timestamp(msg_id, "published", (timestamp, topic))
                add_timestamp(msg_id, "published", (timestamp))
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
                # add_timestamp(None, "grafted", (timestamp, topic, peer_id))
                add_timestamp(None, "grafted", (timestamp))
            elif "GossipSub: Pruned" in log_content:
                ext = extract_data(log_content)
                peer_id = ext[1]
                topic = ext[0]
                # add_timestamp(None, "pruned", (timestamp, topic, peer_id))
                add_timestamp(None, "pruned", (timestamp))
            elif "GossipSub: Joined" in log_content:
                ext = extract_data(log_content)
                topic = ext[0]
                # add_timestamp(None, "joined", (timestamp, topic))
                add_timestamp(None, "joined", (timestamp))
            elif "GossipSub: Left" in log_content:
                ext = extract_data(log_content)
                topic = ext[0]
                # add_timestamp(None, "left", (timestamp, topic))
                add_timestamp(None, "left", (timestamp))
            elif "GossipSub: Peer Removed" in log_content:
                ext = extract_data(log_content)
                peer_id = ext[0]
                # add_timestamp(None, "removed", (timestamp, peer_id))
                add_timestamp(None, "removed", (timestamp))
            elif "GossipSub: Peer Added" in log_content:
                ext = extract_data(log_content)
                peer_id = ext[0]
                # add_timestamp(None, "added", (timestamp, peer_id))
                add_timestamp(None, "added", (timestamp))
            elif "GossipSub: Throttled" in log_content:
                ext = extract_data(log_content)
                peer_id = ext[0]
                # add_timestamp(None, "throttled", (timestamp, peer_id))
                add_timestamp(None, "throttled", (timestamp))
            elif "GossipSubRPC:" in log_content:
                ext = extract_data(log_content)
                if "Publish" in log_content:
                    msg_id = ext[1]
                    topic = ext[0]
                    if "Received" in log_content:
                        # add_timestamp(msg_id, "rpcs_received", (timestamp, topic))
                        add_timestamp(msg_id, "rpcs_received", (timestamp))
                    elif "Sent" in log_content:
                        # add_timestamp(msg_id, "rpcs_sent", (timestamp, topic))
                        add_timestamp(msg_id, "rpcs_sent", (timestamp))
                elif "IHAVE" in log_content:
                    topic = ext[0]
                    if "Received" in log_content:
                        for msg_id in ext[1]:
                            # add_timestamp(msg_id, "ihaves_received", (timestamp, topic))
                            add_timestamp(msg_id, "ihaves_received", (timestamp))
                    elif "Sent" in log_content:
                        for msg_id in ext[1]:
                            # add_timestamp(msg_id, "ihaves_sent", (timestamp, topic))
                            add_timestamp(msg_id, "ihaves_sent", (timestamp))
                elif "IWANT" in log_content:
                    if "Received" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(msg_id, "iwants_received", (timestamp))
                    elif "Sent" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(msg_id, "iwants_sent", (timestamp))
                elif "IDONTWANT" in log_content:
                    if "Received" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(msg_id, "idontwants_received", (timestamp))
                    elif "Sent" in log_content:
                        for msg_id in ext[0]:
                            add_timestamp(msg_id, "idontwants_sent", (timestamp))
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
                        # add_timestamp(msg_id, "iannounces_received", (timestamp, topic))
                        add_timestamp(msg_id, "iannounces_received", (timestamp))
                    elif "Sent" in log_content:
                        # add_timestamp(msg_id, "iannounces_sent", (timestamp, topic))
                        add_timestamp(msg_id, "iannounces_sent", (timestamp))
        else:
            raise Exception("Couldn't match pattern for timestamps")

    return id, timelines


def embed_extracted_data(data, h5grp):
    for key in data:
        if key == "msgs":
            for msg_id in data["msgs"]:
                msggrp = h5grp.create_group(msg_id)
                for k in data["msgs"][msg_id]:
                    msggrp.create_dataset(k, data=data["msgs"][msg_id][k])
        else:
            h5grp.create_dataset(key, data=data[key])


def extract_node_timelines(folder, count, subgrp):
    pbar = tqdm(total=count)
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = []
        for id in range(count):
            futures.append(ex.submit(read_node_logs, folder, id))

        for future in as_completed(futures):
            id, extracted_data = future.result()
            subsubgrp = subgrp.create_group(f"node{id}")
            embed_extracted_data(extracted_data, subsubgrp)
            pbar.update(1)

    pbar.close()


if __name__ == "__main__":
    count = int(sys.argv[1])

    announce_list = [0, 7, 8]
    size_list = [128, 256, 512, 1024, 2048, 4096]
    num_list = [2, 4, 8, 16, 32]

    f = h5py.File("timelines.hdf5", "w")

    # read all simulations
    for announce in announce_list:
        grp = f.create_group(f"DANN{announce}")
        for msg_size in size_list:
            subgrp = grp.create_group(f"{msg_size}-{1}")
            timeline_key = f"{msg_size}-{announce}-1"
            print(f"Reading logs for {timeline_key}")
            extract_node_timelines(f"shadow-{timeline_key}.data", count, subgrp)

        for num_msgs in num_list:
            subgrp = grp.create_group(f"{128}-{num_msgs}")
            timeline_key = f"128-{announce}-{num_msgs}"
            print(f"Reading logs for {timeline_key}")
            extract_node_timelines(f"shadow-{timeline_key}.data", count, subgrp)
    f.close()
