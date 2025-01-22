import re
import datetime
import numpy

# Define the updated regex pattern
line_pattern = r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{6})\s+(.*)"
rx_pattern = r"from (\S+)(?=:)\s*:\s*(\d+)"
BASE_PATH = "./shadow.data/hosts/node"
STDOUT_LOGFILE = "/pubsub-shadow.1000.stdout"

timestamps = []


# Open the file and read it line by line
def read_node_logs(id):
    rx = []
    tx = []
    with open(
        BASE_PATH + str(id) + STDOUT_LOGFILE, "r", encoding="utf-8", errors="replace"
    ) as f:
        for line in f:
            dups = 0
            match = re.match(line_pattern, line.strip())
            if match:
                log_date_time = match.group(1)  # Date (YYYY/MM/DD)
                log_content = match.group(2)  # Log content

                timestamp = datetime.strptime(
                    log_date_time, "%Y/%m/%d %H:%M:%S.%f"
                ).timestamp()

                timestamps.append(timestamp)

                if "Total numbe of duplicates received" in log_content:
                    new_num_dups = int(log_content.split(": ")[1])
                    if new_num_dups > dups:
                        dups = new_num_dups
                elif "Received a message from" in log_content:
                    rxmatch = re.match(rx_pattern, log_content.strip())
                    if rxmatch:
                        log_from = rxmatch.group(1)
                        log_size = rxmatch.group(2)
                        rx.append(
                            {"from": log_from, "size": log_size,
                                "timestamp": timestamp}
                        )
                    else:
                        raise Exception(
                            'Couldn\'t match pattern for "Received Message"'
                        )
                elif "Published message by node" in log_content:
                    tx.append({"from": id, "timestamp": timestamp})
            else:
                raise Exception(
                    'Couldn\'t match pattern for "Received Message"')
    return {"rx": rx, "tx": tx, "dups": dups}


def extract_all_logs(count):
    extracted_data = {}
    for id in range(count):
        extracted_data[id] = read_node_logs(id)

    for id in extracted_data:
        if len(extracted_data[id]["tx"]) > 0:
            print(id, extracted_data[id]["tx"])


if __name__ == "__main__":
    extract_all_logs(5000)
