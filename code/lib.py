import datetime
import json
import sys
import re

#import pybgpstream

RIPE_RIS = [
    "rrc00",
    "rrc01",
    "rrc03",
    "rrc04",
    "rrc05",
    "rrc06",
    "rrc07",
    "rrc10",
    "rrc11",
    "rrc12",
    "rrc13",
    "rrc14",
    "rrc15",
    "rrc16",
    "rrc17",
    "rrc18",
    "rrc19",
    "rrc20",
    "rrc21",
    "rrc22",
    "rrc23",
    "rrc24",
    "rrc25",
    "rrc26",
]
ROUTE_VIEWS = [
    "route-views.amsix",
    "route-views.bknix",
    "route-views.chicago",
    "route-views.chile",
    "route-views.eqix",
    "route-views.flix",
    "route-views.fortaleza",
    "route-views.gixa",
    "route-views.gorex",
    "route-views.isc",
    "route-views.kixp",
    "route-views.linx",
    "route-views.mwix",
    "route-views.napafrica",
    "route-views.nwax",
    "route-views.ny",
    "route-views.perth",
    "route-views.phoix",
    "route-views.peru",
    "route-views.rio",
    "route-views.sfmix",
    "route-views.sg",
    "route-views.soxrs",
    "route-views.sydney",
    "route-views.telxatl",
    "route-views.uaeix",
    "route-views.wide",
    "route-views2",
    "route-views2.saopaulo",
    "route-views3",
    "route-views4",
    "route-views5",
    "route-views6",
]


def parse_line_string_to_json(input_string):
    line_data = input_string.split("|")

    # Create a dictionary with the desired JSON structure
    json_data = {
        "record_type": line_data[0],
        "type": line_data[1],
        "timestamp": float(line_data[2]),
        "project": line_data[3],
        "collector": line_data[4],
        "router": line_data[5] if line_data[5] else None,
        "router_ip": line_data[6] if line_data[6] else None,
        "peer_asn": int(line_data[7]),
        "peer_address": line_data[8],
        "prefix": line_data[9],
        "next-hop": line_data[10],
        "as-path": line_data[11].split(),
        "communities": line_data[12].split(),
        "old-state": line_data[13] if line_data[13] else None,
        "new-state": line_data[14] if line_data[14] else None,
    }

    return json_data


def is_utc_datetime(datetime_str):
    """
    Check if the provided datetime string is in UTC datetime format.

    Args:
        datetime_str (str): The datetime string to check.

    Returns:
        bool: True if the datetime string is in UTC datetime format, False otherwise.
    """
    try:
        datetime.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return True
    except (ValueError, TypeError):
        return False


def is_unix_timestamp(datetime_str):
    """
    Check if the provided datetime string is a Unix timestamp.

    Args:
        datetime_str (str): The datetime string to check.

    Returns:
        bool: True if the datetime string is a valid Unix timestamp, False otherwise.
    """
    try:
        datetime.datetime.utcfromtimestamp(float(datetime_str))
        return True
    except (ValueError, TypeError):
        return False


def is_timestamp_between(start_timestamp, end_timestamp, check_timestamp):
    """Check if a given timestamp is between two other timestamps.

    Args:
        start_timestamp (str): Start timestamp in ISO 8601 or UTC datetime format.
        end_timestamp (str): End timestamp in ISO 8601 or UTC datetime format.
        check_timestamp (str): Timestamp to check in ISO 8601 or UTC datetime format.

    Returns:
        bool: True if check_timestamp is between start_timestamp and end_timestamp, False otherwise.
    """

    if is_utc_datetime(start_timestamp):
        start_timestamp = datetime_str_to_timestamp(start_timestamp)
    if is_utc_datetime(end_timestamp):
        end_timestamp = datetime_str_to_timestamp(end_timestamp)
    if is_utc_datetime(check_timestamp):
        check_timestamp = datetime_str_to_timestamp(check_timestamp)

    if start_timestamp <= end_timestamp:
        return start_timestamp <= check_timestamp <= end_timestamp
    else:
        return start_timestamp <= check_timestamp or check_timestamp <= end_timestamp


def unix_timestamp_to_utc_datetime(timestamp, datetime_format=False):
    """Convert a Unix timestamp to a UTC datetime object.

    Args:
        timestamp (int): Unix timestamp.
        datetime_format (bool): If true returns a datetime object

    Returns:
        datetime.datetime: A datetime object or string in UTC.
    """
    utc_datetime = datetime.datetime.utcfromtimestamp(timestamp)
    if datetime_format:
        return utc_datetime
    formatted_dt = utc_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return formatted_dt


def datetime_str_to_timestamp(datetime_str):
    """Convert a datetime string in ISO 8601 format to a Unix timestamp.

    Args:
        datetime_str (str): Datetime string in ISO 8601 format.

    Returns:
        int: Unix timestamp.
    """
    utc_datetime = datetime.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    utc_datetime = utc_datetime.replace(tzinfo=datetime.timezone.utc)
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    delta = utc_datetime - epoch
    timestamp = delta.total_seconds()
    return int(timestamp)


def download_bgpstream(
    collectors=["rrc00"],
    start_time="2023-04-26T15:38:23.449190Z",
    end_time="2023-05-04T14:08:23.504529Z",
    prefixes=["138.185.229.0/24"],
    record_type="ribs",
):
    """Return a list of BGPStream objects for a given time interval, collector, prefix and record type.

    Args:
        collectors (List(str)): Names of the BGP collectors.
        start_time (str): Start time of the interval in ISO 8601 format.
        end_time (str): End time of the interval in ISO 8601 format.
        prefix (List)): List of prefixes to filter the BGP updates.
        record_type (str): Type of BGP updates to read - 'ribs' or 'updates'.

    Returns:
        A list of BGPStream objects configured with the given parameters.
    """
    FILTER = "prefix more {}"

    start_time = datetime_str_to_timestamp(start_time)
    end_time = datetime_str_to_timestamp(end_time)

    filter_string = "ipversion 4"
    for pfx in prefixes:
        filter_string += f" and {FILTER.format(pfx)}"

    stream = pybgpstream.BGPStream(
        from_time=start_time,
        until_time=end_time,
        filter=filter_string,
        record_type=record_type,
        collectors=collectors,
    )

    elem_list = []
    for elem in stream:
        elem_list.append(parse_line_string_to_json(str(elem).replace('\"', '"')))

    return elem_list


def as_paths_in_interval_time(
    records,
    start_time=None,
    end_time=None,
):
    """Return a list of unique AS-paths present in a given time interval of BGP dump file.

    Args:
        start_time (str): Start time of the interval in ISO 8601 format.
        end_time (str): End time of the interval in ISO 8601 format.
        records (list): List of records in Dict format".

    Returns:
        list: A list of unique AS-paths present in the given time interval of the BGP dump file.
    """

    as_paths_list = []

    if start_time == None:
        start_time = records[0]["timestamp"]
    if end_time == None:
        end_time = records[-1]["timestamp"]

    for record in records:
        if "None" in record["as-path"] or record["type"] != "A":
            continue
        if (
            is_timestamp_between(start_time, end_time, int(record["timestamp"]))
            and record["as-path"] not in as_paths_list
        ):
            as_paths_list.append(list(map(int, record["as-path"])))

    return as_paths_list


def number_of_updates_between_interval(
    records, start_time=None, end_time=None, filter_record_type=["P"]
):
    """
    Counts the number of updates within a specified time interval from a BGP dump file.

    Args:
        start_time (int): The start timestamp of the interval.
        end_time (int): The end timestamp of the interval.
        records (list): List of records in Dict format".
        filter_record_type (list, optional): List of record types to filter. Defaults to an empty list.

    Returns:
        int: The number of updates within the specified time interval.

    """
    update_list = []

    if start_time == None:
        start_time = records[0]["timestamp"]
    if end_time == None:
        end_time = records[-1]["timestamp"]

    for record in records:
        if record["type"] in filter_record_type:
            continue
        if is_timestamp_between(start_time, end_time, int(record["timestamp"])):
            update_list.append(record)

    return len(update_list)


def _get_next_hop_from_as_path(as_path, peering_asn=47065):
    """
    Extracts the next hop from the AS path.

    Args:
        as_path (list): The AS path represented as a list of AS numbers.
        peering_asn (int, optional): The peering ASN. Defaults to 47065.

    Returns:
        int: The next hop AS number.

    Raises:
        SystemExit: If the AS path is invalid.
    """
    if int(as_path[-2]) == peering_asn:
        return int(as_path[-3])
    else:
        sys.exit("Invalid AS-PATH")


def get_next_hop_set(list_of_as_path, peering_asn=47065):
    """
    Retrieves the unique set of next hop AS numbers from a list of AS paths.

    Args:
        list_of_as_path (list): A list of AS paths, where each AS path is represented as a list of AS numbers.
        peering_asn (int, optional): The peering ASN. Defaults to 47065.

    Returns:
        list: A list of unique next hop AS numbers.
    """
    next_hop_list = []
    for as_path in list_of_as_path:
        next_hop = _get_next_hop_from_as_path(as_path, peering_asn)
        if next_hop not in next_hop_list:
            next_hop_list.append(next_hop)
    return next_hop_list


def read_bgpdump_file(bgpdump_file, start_timestamp=None, end_timestamp=None):
    """
    Read a BGP dump file in JSON format and filter the records based on the provided start and end timestamps.

    Args:
        bgpdump_file (str): The path to the BGP dump file.
        start_timestamp (str, optional): Start timestamp for filtering the records. If provided, only records with timestamps greater than or equal to this value will be included.
        end_timestamp (str, optional): End timestamp for filtering the records. If provided, only records with timestamps less than or equal to this value will be included.
        utc_format (bool, optional): Flag indicating whether the timestamps are in UTC format. If True, timestamps will be converted to Unix timestamps for comparison.
    Returns:
        list: A list of BGP records filtered based on the provided timestamps.
    """

    fd = open(bgpdump_file, "r")
    data = json.load(fd)
    fd.close()
    records = []

    if is_utc_datetime(start_timestamp):
        start_timestamp = datetime_str_to_timestamp(start_timestamp)
    if is_utc_datetime(end_timestamp):
        end_timestamp = datetime_str_to_timestamp(end_timestamp)

    for rec in data:
        if start_timestamp and rec["timestamp"] < start_timestamp:
            continue
        if end_timestamp and rec["timestamp"] > end_timestamp:
            continue
        records.append(rec)

    _check_records_sorted_by_timestamp(records)

    return records


def indexed_routes_by_peer_address(records, filter_record_type=["P"]):
    """
    Indexes routes by peer address.

    Iterates through the provided records and creates a dictionary where each peer address is associated
    with the corresponding record.

    Args:
        records (list): List of records containing route information.
        filter_record_type (list, optional): List of record types to filter. Defaults to [].

    Returns:
        dict: A dictionary where each peer address is mapped to the corresponding record.
    """
    indexed_updates = {}

    # Note that only the last announcement (or withdraw) is saved from each session (peer, collector)
    for record in records:
        if record["type"] in filter_record_type:
            continue
        indexed_updates[record["peer_address"]] = record

    return indexed_updates


def _check_records_sorted_by_timestamp(records):
    """
    Check if the records are sorted by timestamp.

    This function takes a list of records and checks if they are sorted by timestamp in ascending order.
    If any record is found to have a timestamp earlier than the previous record, an error message is printed
    and the program exits.

    Args:
        records (list): A list of dictionaries representing records.
            Each record dictionary should have a "timestamp" key with a timestamp value.

    Raises:
        SystemExit: If the records are not sorted by timestamp.

    """
    for i_rec in range(1, len(records)):
        if records[i_rec]["timestamp"] < records[i_rec - 1]["timestamp"]:
            sys.exit("Error, records not sorted by timestamp")

def check_inconsistency(indexed_updates):
    """
    Check for inconsistencies in indexed updates.

    This function iterates over the `indexed_updates` dictionary and checks for inconsistencies
    based on the values of the "peer_asn" and "type" keys in each record. It returns two lists:
    `list_of_inconsistency_ann` and `list_of_inconsistency_with`, containing the inconsistent records.

    Args:
        indexed_updates (dict): A dictionary containing indexed updates.

    Returns:
        tuple: A tuple containing two lists:
            - list_of_inconsistency_ann (list): A list of records with inconsistency announcements.
            - list_of_inconsistency_with (list):  A list of records with inconsistency withdraws.
    """

    list_of_inconsistency_ann = []
    list_of_inconsistency_with = []

    for record in indexed_updates.values():
        for record_comp in indexed_updates.values():
            if (
                record["peer_asn"] == record_comp["peer_asn"]
                and record["type"] != record_comp["type"]
            ):

                if record in list_of_inconsistency_with and record_comp in list_of_inconsistency_ann:
                    continue
                if record_comp in list_of_inconsistency_with and record in list_of_inconsistency_ann:
                    continue

                if record["type"] == "A":
                    list_of_inconsistency_ann.append(record)
                    list_of_inconsistency_with.append(record_comp)
                else:
                    list_of_inconsistency_ann.append(record_comp)
                    list_of_inconsistency_with.append(record)

    assert len(list_of_inconsistency_ann) == len(list_of_inconsistency_with)

    return (list_of_inconsistency_ann, list_of_inconsistency_with)
