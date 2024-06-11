#!/usr/bin/env python3

import lib
from collections import defaultdict
import pickle
import sys
import os
import re
import json
import argparse

BAD_ORIGIN = '47065'
GOOD_ORIGIN = '61574'

def check_intersection(asn_t, p2, p5, p3, p1):
    intersection = list(set(p2[asn_t]) & set(p5[asn_t]) & set(p3[asn_t]) & set(p1[asn_t]))
    for i in range(0, len(intersection)):
        if int(intersection[i]) == int(asn_t):
            continue
        if int(intersection[i]) != int(GOOD_ORIGIN) and int(intersection[i]) != int(BAD_ORIGIN):
            return True
    return False


def remove_adjacent_duplicates(input_list):
    if not input_list:
        return []

    # Initialize a new list with the first element
    result = [input_list[0]]

    # Iterate through the input list starting from the second element
    for i in range(1, len(input_list)):
        # Check if the current element is different from the previous one
        if input_list[i] != input_list[i - 1]:
            result.append(input_list[i])

    return result

def complete_routes(route_per_asn):
    temp = defaultdict(list)
    route_per_asn = dict(sorted(route_per_asn.items(), key=lambda x: len(x[1])))
    for asn in route_per_asn:
        as_list = route_per_asn[asn]
        for ientry in range(0, len(as_list)):
            if (as_list[ientry] not in route_per_asn) and (as_list[ientry] not in temp):
                temp[as_list[ientry]] = as_list[ientry:]
    for asn in temp:
        route_per_asn[asn] = temp[asn]
    return route_per_asn

def parse_routes(route_per_asn, as_list):
    max = 0
    for asn in as_list:
        if asn in route_per_asn:
            route_per_asn[asn] = remove_adjacent_duplicates(route_per_asn[asn])
            if len(route_per_asn[asn]) > max:
                max = len(route_per_asn[asn])
        else:
            route_per_asn[asn] = []

    return (route_per_asn, max)


def add_appends(data):
    for asn in data:
        if len(data[asn]) > 0 and data[asn][-1].isdigit():
            if int(data[asn][-1]) == int(GOOD_ORIGIN):
                data[asn].extend(6 * [GOOD_ORIGIN])
    return data

# find neighbors, using asrel dataset
def find_neighbors(asn_t, p5_neighbor):

    #caida asrel dataset
    file_path = "../data/20231201.as-rel.txt"

    pattern = r'^(\d+)\|(\d+)\|(\d+)$'

    with open(file_path, 'r') as file:
        input_string = file.read()

    matches = re.findall(pattern, input_string, re.MULTILINE)

    asn_t_providers = []
    asn_t_customers = []
    asn_t_peers = []

    for match in matches:
        if asn_t in match:
            if int(match[2]) == 0 and asn_t == match[0]:
                asn_t_peers.append(match[1])
            elif int(match[2]) == 0 and asn_t == match[1]:
                asn_t_peers.append(match[0])
            elif int(match[2]) == -1 and asn_t == match[0]:
                asn_t_customers.append(match[1])
            else:
                asn_t_providers.append(match[0])

    # return neighbors with similar or higher preference
    if p5_neighbor in asn_t_providers:
        return asn_t_providers + asn_t_customers + asn_t_peers

    if p5_neighbor in asn_t_peers:
        return asn_t_peers + asn_t_customers

    if p5_neighbor in asn_t_customers:
        return asn_t_customers

    return []

def neighbors_prefix_usage(asn_t, data, origin):
    if len(data[asn_t]) < 2:
        return False
    p5_neighbor = data[asn_t][1]
    neighbors = find_neighbors(asn_t, p5_neighbor)
    for n in neighbors:
        if not n in data or len(data[n]) < 2:
            return False
        if data[n][-1] == origin:
            return True
    return False

def assert_one_classification(asn_t, data, class_t, class_dict):
    for asn in data[asn_t]:
        if asn == asn_t:
            continue
        if asn not in class_dict:
            return False
        if class_dict[asn] in class_t:
            return True
    return False

def assert_all_classification(asn_t, data, class_t, class_dict):
    for asn in data[asn_t]:
        if asn == GOOD_ORIGIN or asn == BAD_ORIGIN:
            continue
        if asn == asn_t:
            continue
        if asn not in class_dict:
            return False
        if class_dict[asn] not in class_t:
            return False
    return True


def get_records(base_bgp_dump, start_timestamp, end_timestamp, prefix):
    records = lib.read_bgpdump_file(
        bgpdump_file=base_bgp_dump,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )

    pfx_routes = defaultdict(list)
    for rec in records:
        if rec["prefix"] == prefix and rec["type"] == "A":
            pfx_routes[rec["peer_asn"]] = rec["as-path"]
    return pfx_routes


def classification_phase1(asn_t, class_dict, p2, p4, p5, p3, p1):
    if not asn_t.isdigit():
        return

    if asn_t not in class_dict:
        if len(p2[asn_t]) > 0 and int(p2[asn_t][-1]) == int(BAD_ORIGIN) and \
        len(p4[asn_t]) > 0 and int(p4[asn_t][-1]) == int(BAD_ORIGIN) and \
        len(p5[asn_t]) > 0 and int(p5[asn_t][-1]) == int(BAD_ORIGIN) and \
        len(p3[asn_t]) > 0 and int(p3[asn_t][-1]) == int(GOOD_ORIGIN) and \
        len(p1[asn_t]) > 0 and int(p1[asn_t][-1]) == int(BAD_ORIGIN):
            class_dict[asn_t] = "ignore-roa"

        elif len(p2[asn_t]) > 0 and int(p2[asn_t][-1]) == int(BAD_ORIGIN) and \
            len(p4[asn_t]) > 0 and int(p4[asn_t][-1]) == int(BAD_ORIGIN) and \
            len(p5[asn_t]) > 0 and int(p5[asn_t][-1]) == int(GOOD_ORIGIN) and \
            len(p3[asn_t]) > 0 and int(p3[asn_t][-1]) == int(GOOD_ORIGIN) and \
            len(p1[asn_t]) > 0 and int(p1[asn_t][-1]) == int(BAD_ORIGIN):
            #p2[asn_t] == p1[asn_t]:
            class_dict[asn_t] = "prefer-valid"

        elif len(p2[asn_t]) > 0 and int(p2[asn_t][-1]) == int(BAD_ORIGIN) and \
            len(p4[asn_t]) == 0 and \
            len(p5[asn_t]) > 0 and int(p5[asn_t][-1]) == int(GOOD_ORIGIN) and \
            len(p3[asn_t]) > 0 and int(p3[asn_t][-1]) == int(GOOD_ORIGIN) and \
            len(p1[asn_t]) > 0 and int(p1[asn_t][-1]) == int(BAD_ORIGIN):
            #p2[asn_t] == p1[asn_t]:
            class_dict[asn_t] = "drop-invalid"
        else:
            class_dict[asn_t] = "unknown"

def classification_phase2(asn_t, class_dict, corner_cases, total_corner_case, p2, p4, p5, p3, p1):
    if not asn_t.isdigit():
        return
    if class_dict[asn_t] == "drop-invalid":
        total_corner_case[asn_t] = "drop-invalid"
        if assert_one_classification(asn_t, p2, ["drop-invalid", "unknown", "prefer-valid"], class_dict):
            class_dict[asn_t] = "unknown-protected"
            corner_cases[asn_t] = ("drop-invalid", "unknown-protected")

    if class_dict[asn_t] == "ignore-roa":
        total_corner_case[asn_t] = "ignore-roa"
        if assert_all_classification(asn_t, p3, ["drop-invalid", "prefer-valid"], class_dict) or \
            neighbors_prefix_usage(asn_t, p5, GOOD_ORIGIN):
            class_dict[asn_t] = "ignore-roa"
        else:
            class_dict[asn_t] = "prefer-ignore"
            corner_cases[asn_t] = ("ignore-roa", "prefer-ignore")

    if class_dict[asn_t] == "prefer-valid":
        total_corner_case[asn_t] = "prefer-valid"
        if check_intersection(asn_t, p2, p5, p3, p1):
            class_dict[asn_t] = "prefer-neighbor/prefer-valid"
            corner_cases[asn_t] = ("prefer-valid", "prefer-provider/prefer-valid")
        elif assert_all_classification(asn_t, p4, ["ignore-roa"], class_dict) or \
            neighbors_prefix_usage(asn_t, p5, BAD_ORIGIN):
            class_dict[asn_t] = "prefer-valid"
        else:
            class_dict[asn_t] = "prefer-ignore"
            corner_cases[asn_t] = ("prefer-valid", "prefer-ignore")

def create_parser():
    desc = """Process BGP measurements"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--measurement",
        dest="measurement",
        action="store",
        required=True,
        help="Name of target measurement",
    )
    parser.add_argument(
        "--city",
        dest="city",
        action="store",
        required=True,
        help="Measurement location",
    )
    return parser

def main():

    parser = create_parser()
    opts = parser.parse_args()

    with open("../config.json", "r") as config_fd:
        config = json.load(config_fd)

    start_time = config[opts.measurement]["location"][opts.city]["start"]
    end_time = config[opts.measurement]["location"][opts.city]["end"]
    base_dump = os.path.join("../data/", config[opts.measurement]["bgpdump"])

    nicbr_dump = f"{base_dump}_roa_sorted.json"

    p2 = get_records(nicbr_dump, start_time, end_time, "138.185.228.0/24")

    p4 = get_records(nicbr_dump, start_time, end_time, "138.185.229.0/24")

    p5 = get_records(nicbr_dump, start_time, end_time,"138.185.230.0/24")

    p3 = get_records(nicbr_dump, start_time, end_time, "138.185.231.0/24")

    p2 = complete_routes(p2)
    p4 = complete_routes(p4)
    p5 = complete_routes(p5)
    p3 = complete_routes(p3)

    arin_dump = f"{base_dump}_no_roa_sorted.json"

    p1 = get_records(arin_dump, start_time, end_time, "204.9.170.0/24")


    p1 = complete_routes(p1)


    as_list = []
    for d in [p2, p4, p5, p3, p1]:
        for key in d:
            if key not in as_list:
                as_list.append(key)

    p2, max_p2 = parse_routes(p2, as_list)
    p4, max_p4 = parse_routes(p4, as_list)
    p5, max_p5 = parse_routes(p5, as_list)
    p3, max_p3 = parse_routes(p3, as_list)
    p1, max_p1 = parse_routes(p1, as_list)

    max_ = max([max_p2, max_p4, max_p5, max_p3, max_p1])

    class_dict = {}

    # PEERING and Vultr's ASNs
    class_dict[GOOD_ORIGIN] = "ignore-roa"
    class_dict[BAD_ORIGIN] = "ignore-roa"
    class_dict["20473"] = "ignore-roa"

    corner_cases = {}

    total_cases_phase1 = {}

    for i in range(max_-1, -1, -1):
        for asn in p2:
            if len(p2[asn]) > i:
                classification_phase1(p2[asn][i], class_dict, p2, p4, p5, p3, p1)
            if len(p4[asn]) > i:
                classification_phase1(p4[asn][i], class_dict, p2, p4, p5, p3, p1)
            if len(p5[asn]) > i:
                classification_phase1(p5[asn][i], class_dict, p2, p4, p5, p3, p1)
            if len(p3[asn]) > i:
                classification_phase1(p3[asn][i], class_dict, p2, p4, p5, p3, p1)

    for i in range(max_-1, -1, -1):
        for asn in p2:
            if len(p2[asn]) > i:
                classification_phase2(p2[asn][i], class_dict, corner_cases, total_cases_phase1, p2, p4, p5, p3, p1)
            if len(p4[asn]) > i:
                classification_phase2(p4[asn][i], class_dict, corner_cases, total_cases_phase1, p2, p4, p5, p3, p1)
            if len(p5[asn]) > i:
                classification_phase2(p5[asn][i], class_dict, corner_cases, total_cases_phase1, p2, p4, p5, p3, p1)
            if len(p3[asn]) > i:
                classification_phase2(p3[asn][i], class_dict, corner_cases, total_cases_phase1, p2, p4, p5, p3, p1)

    #return appends after classification
    #p2 = add_appends(p2)
    #p4 = add_appends(p4)
    #p5 = add_appends(p5)
    #p3 = add_appends(p3)
    #p1 = add_appends(p1)

    location = opts.city

    if not os.path.exists(location):
        os.makedirs(location)
    print(class_dict)
    file = open(os.path.join(location, "classification"), 'wb')
    pickle.dump(class_dict, file)

    file_cases = open(os.path.join(location, "corner_cases"), 'wb')
    pickle.dump(corner_cases, file_cases)

    file_first_phase = open(os.path.join(location, "total_cases_phase1"), 'wb')
    pickle.dump(total_cases_phase1, file_first_phase)

    file_p2 = open(os.path.join(location, "p2"), 'wb')
    pickle.dump(p2, file_p2)
    file_p4 = open(os.path.join(location, "p4"), 'wb')
    pickle.dump(p4, file_p4)
    file_p5 = open(os.path.join(location, "p5"), 'wb')
    pickle.dump(p5, file_p5)
    file_p3 = open(os.path.join(location, "p3"), 'wb')
    pickle.dump(p3, file_p3)
    file_p1 = open(os.path.join(location, "p1"), 'wb')
    pickle.dump(p1, file_p1)

if __name__ == "__main__":
    sys.exit(main())
