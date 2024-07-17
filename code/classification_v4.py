#!/usr/bin/env python3

import lib
from collections import defaultdict
import pickle
import sys
import os
import re
import json
import argparse
from multiprocessing import Pool

BAD_ORIGIN = "61574" ## change after new exp
GOOD_ORIGIN = "47065"

MAX = 8


def check_intersection(asn_t, p2, p5, p3, p1):
    intersection = list(
        set(p2[asn_t]) & set(p5[asn_t]) & set(p3[asn_t]) & set(p1[asn_t])
    )
    for i in range(0, len(intersection)):
        if int(intersection[i]) == int(asn_t):
            continue
        if int(intersection[i]) != int(GOOD_ORIGIN) and int(intersection[i]) != int(
            BAD_ORIGIN
        ):
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
def find_neighbors(asn_t):

    # caida asrel dataset
    file_path = "../data/20231201.as-rel.txt"

    pattern = r"^(\d+)\|(\d+)\|(\d+)$"

    with open(file_path, "r") as file:
        input_string = file.read()

    matches = re.findall(pattern, input_string, re.MULTILINE)

    neighbors = []
    for match in matches:
        if asn_t in match:
            if asn_t == match[0]:
                neighbors.append(match[1])
            elif asn_t == match[1]:
                neighbors.append(match[0])
    return neighbors



def relationship(asn1, asn2):

    # caida asrel dataset
    file_path = "../data/20231201.as-rel.txt"

    pattern = r"^(\d+)\|(\d+)\|(\d+)$"

    with open(file_path, "r") as file:
        input_string = file.read()

    matches = re.findall(pattern, input_string, re.MULTILINE)

    for match in matches:
        if asn1 in match and asn2 in match:
            if asn1 == match[0] and asn2 == match[1] and int(match[2]) == 0:
                return "p2p"
            elif asn1 == match[1] and asn2 == match[0] and int(match[2]) == 0:
                return "p2p"
            elif asn1 == match[0] and asn2 == match[1] and int(match[2]) == -1:
                return "prov-cli"
            elif asn1 == match[1] and asn2 == match[0] and int(match[2]) == -1:
                return "cli-prov"
            else:
                return "p2p"

def is_valley_free(route, asn_t):
    index = route.index("47065") # get origin index in the route
    route_wo_origin = route[:index] # remove origin ("47065" or "47065, 61574")
    # add asn_t on route to include asn target on valley free checking
    if len(route_wo_origin) > 0 and route_wo_origin[0] != asn_t:
        route_wo_origin.insert(0, asn_t)

    if len(route_wo_origin) < 3:
        return True

    # check wether valley-free is violated


    for i in range(len(route_wo_origin)-3, 0):
        if relationship(route_wo_origin[i], route_wo_origin[i+1]) == "prov-cli" \
        and relationship(route_wo_origin[i+1], route_wo_origin[i+2]) == "cli-prov":
            return False

        if relationship(route_wo_origin[i], route_wo_origin[i+1]) == "p2p" \
        and relationship(route_wo_origin[i+1], route_wo_origin[i+2]) == "p2p":
            return False

        if relationship(route_wo_origin[i], route_wo_origin[i+1]) == "prov-cli" \
        and relationship(route_wo_origin[i+1], route_wo_origin[i+2]) == "p2p":
            return False

        if relationship(route_wo_origin[i], route_wo_origin[i+1]) == "p2p" \
        and relationship(route_wo_origin[i+1], route_wo_origin[i+2]) == "cli-prov":
            return False

    return True


def check_target_receive_route(asn_t, route, origin):
    if len(route[asn_t]) < 2:
        return False
    neighbors = find_neighbors(asn_t)
    candidates = []
    for n in neighbors:
        if not n in route or len(route[n]) < 2:
            continue
        if route[n][-1] == origin:
            candidates.append(n)

    #check valley free for candidates
    if len(candidates) == 0:
        return False
    for c in candidates:
        if not is_valley_free(route[c], asn_t):
            return False
    return True


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


def get_stable_trace(asn_tracerout_list):
    if len(asn_tracerout_list) > 1:
        if asn_tracerout_list[-1] == asn_tracerout_list[-2]:
            return list(map(str, asn_tracerout_list[-1]))
    return []


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


def integrate_traces(traceroutes, pfx_routes, start_time, end_time, prefix):
    mapping_asn_traces = defaultdict(list)
    for trace in traceroutes:
        if (
            lib.is_timestamp_between(start_time, end_time, trace["endtime"])
            and prefix == trace["dst_addr"]
        ):
            mapping_asn_traces[str(trace["origin_asn"])].append(trace["result"])
    asn_trace = {}

    for asn in mapping_asn_traces:
        asn_trace[asn] = get_stable_trace(mapping_asn_traces[asn])

    for asn in asn_trace:
        if asn.isdigit() and (str(asn) not in pfx_routes):
            for asn_i in range(0, len(asn_trace[asn])):
                if not asn_trace[asn][asn_i].isdigit():
                    break
                if str(asn_trace[asn][asn_i]) == str(asn):
                    continue
                if str(asn_trace[asn][asn_i]) in pfx_routes:
                    pfx_routes[asn] = (
                        asn_trace[asn][:asn_i] + pfx_routes[asn_trace[asn][asn_i]]
                    )
                    if (
                        pfx_routes[asn][0] != asn
                    ):  # add origin asn in list if it's not there
                        pfx_routes[asn].insert(0, asn)
    return pfx_routes


def classification_phase1(asn_t, class_dict, p2, p4, p5, p3, p1):
    if not asn_t.isdigit():
        return

    if asn_t not in class_dict:
        if (
            len(p2[asn_t]) > 0 and int(p2[asn_t][-1]) == int(BAD_ORIGIN)
            and len(p4[asn_t]) > 0 and int(p4[asn_t][-1]) == int(BAD_ORIGIN)
            and len(p5[asn_t]) > 0 and int(p5[asn_t][-1]) == int(BAD_ORIGIN)
            and len(p3[asn_t]) > 0 and int(p3[asn_t][-1]) == int(GOOD_ORIGIN)
            and len(p1[asn_t]) > 0 and int(p1[asn_t][-1]) == int(BAD_ORIGIN)
        ):
            class_dict[asn_t] = "ignore-roa"

        elif (
            len(p2[asn_t]) > 0 and int(p2[asn_t][-1]) == int(BAD_ORIGIN)
            and len(p4[asn_t]) > 0 and int(p4[asn_t][-1]) == int(BAD_ORIGIN)
            and len(p5[asn_t]) > 0 and int(p5[asn_t][-1]) == int(GOOD_ORIGIN)
            and len(p3[asn_t]) > 0 and int(p3[asn_t][-1]) == int(GOOD_ORIGIN)
            and len(p1[asn_t]) > 0 and int(p1[asn_t][-1]) == int(BAD_ORIGIN)
        ):

            class_dict[asn_t] = "prefer-valid"

        elif (
            len(p2[asn_t]) > 0 and int(p2[asn_t][-1]) == int(BAD_ORIGIN) and len(p4[asn_t]) == 0
            and len(p5[asn_t]) > 0 and int(p5[asn_t][-1]) == int(GOOD_ORIGIN)
            and len(p3[asn_t]) > 0 and int(p3[asn_t][-1]) == int(GOOD_ORIGIN)
            and len(p1[asn_t]) > 0 and int(p1[asn_t][-1]) == int(BAD_ORIGIN)
        ):
            class_dict[asn_t] = "drop-invalid"
        else:
            class_dict[asn_t] = "unknown"


def classification_phase2(
    asn_t, class_dict, corner_cases, total_corner_case, p2, p5, p3, p1
):
    if not asn_t.isdigit():
        return
    if asn_t == "61574" or asn_t == "47065" or asn_t == "20473":
        return
    if class_dict[asn_t] == "drop-invalid":
        total_corner_case[asn_t] = "drop-invalid"
        if assert_one_classification(
            asn_t, p2, ["drop-invalid", "unknown", "prefer-valid"], class_dict
        ):
            class_dict[asn_t] = "unknown-protected"
            corner_cases[asn_t] = ("drop-invalid", "unknown-protected")

    if class_dict[asn_t] == "ignore-roa":
        total_corner_case[asn_t] = "ignore-roa"
        if check_target_receive_route(asn_t, p5, GOOD_ORIGIN):
            class_dict[asn_t] = "ignore-roa"
        else:
            class_dict[asn_t] = "prefer-ignore"
            corner_cases[asn_t] = ("ignore-roa", "prefer-ignore")

    if class_dict[asn_t] == "prefer-valid":
        total_corner_case[asn_t] = "prefer-valid"
        if check_intersection(asn_t, p2, p5, p3, p1):
            class_dict[asn_t] = "prefer-peer/prefer-valid"
            corner_cases[asn_t] = ("prefer-valid", "prefer-peer/prefer-valid")
        elif check_target_receive_route(asn_t, p5, BAD_ORIGIN):
            class_dict[asn_t] = "prefer-valid"
        else:
            class_dict[asn_t] = "prefer-ignore"
            corner_cases[asn_t] = ("prefer-valid", "prefer-ignore")


def classification(args):

    city, time, measurement, traceroutes = args

    start_time = time["start"]
    end_time = time["end"]
    base_dump = os.path.join("../data/", measurement)

    nicbr_dump = f"{base_dump}_roa_sorted.json"

    p2 = get_records(nicbr_dump, start_time, end_time, "138.185.228.0/24")
    p2 = complete_routes(p2)
    p2 = integrate_traces(traceroutes, p2, start_time, end_time, "138.185.228.1")
    p2 = complete_routes(p2)

    p4 = get_records(nicbr_dump, start_time, end_time, "138.185.229.0/24")
    p4 = complete_routes(p4)
    p4 = integrate_traces(traceroutes, p4, start_time, end_time, "138.185.229.1")
    p4 = complete_routes(p4)

    p5 = get_records(nicbr_dump, start_time, end_time, "138.185.230.0/24")
    p5 = complete_routes(p5)
    p5 = integrate_traces(traceroutes, p5, start_time, end_time, "138.185.230.1")
    p5 = complete_routes(p5)

    p3 = get_records(nicbr_dump, start_time, end_time, "138.185.231.0/24")
    p3 = complete_routes(p3)
    p3 = integrate_traces(traceroutes, p3, start_time, end_time, "138.185.231.1")
    p3 = complete_routes(p3)

    arin_dump = f"{base_dump}_no_roa_sorted.json"

    p1 = get_records(arin_dump, start_time, end_time, "204.9.170.0/24")
    p1 = complete_routes(p1)
    p1 = integrate_traces(traceroutes, p2, start_time, end_time, "138.185.228.1") ##change after new exp
    p1 = complete_routes(p1)

    as_list = []
    key_group = set(p2) | set(p4) | set(p5) | set(p3) | set(p1)

    for key in list(key_group):
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
    class_dict["20473"] = "drop-invalid"

    for i in range(max_ - 1, -1, -1):
        for asn in p2:
            if asn in p2 and len(p2[asn]) > i:
                classification_phase1(p2[asn][i], class_dict, p2, p4, p5, p3, p1)
            if asn in p4 and len(p4[asn]) > i:
                classification_phase1(p4[asn][i], class_dict, p2, p4, p5, p3, p1)
            if asn in p5 and len(p5[asn]) > i:
                classification_phase1(p5[asn][i], class_dict, p2, p4, p5, p3, p1)
            if asn in p3 and len(p3[asn]) > i:
                classification_phase1(p3[asn][i], class_dict, p2, p4, p5, p3, p1)

    corner_cases = {}
    total_cases_phase1 = {}
    for i in range(max_ - 1, -1, -1):
        for asn in p2:
            if asn in p2 and len(p2[asn]) > i:
                classification_phase2(
                    p2[asn][i], class_dict, corner_cases, total_cases_phase1, p2, p5, p3, p1,
                )
            if asn in p4 and len(p4[asn]) > i:
                classification_phase2(
                    p4[asn][i], class_dict, corner_cases, total_cases_phase1, p2, p5, p3, p1,
                )
            if asn in p5 and len(p5[asn]) > i:
                classification_phase2(
                    p5[asn][i], class_dict, corner_cases, total_cases_phase1, p2, p5, p3, p1,
                )
            if asn in p3 and len(p3[asn]) > i:
                classification_phase2(
                    p3[asn][i], class_dict, corner_cases, total_cases_phase1, p2, p5, p3, p1,
                )

    # return appends after classification
    p2 = add_appends(p2)
    p4 = add_appends(p4)
    p5 = add_appends(p5)
    p3 = add_appends(p3)
    p1 = add_appends(p1)

    print("len class dict", len(class_dict))

    base_path = os.path.join(f"../dump/{measurement}", city)
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    file = open(os.path.join(base_path, "classification"), "wb")
    pickle.dump(class_dict, file)

    file_p2 = open(os.path.join(base_path, "p2"), "wb")
    pickle.dump(p2, file_p2)
    file_p4 = open(os.path.join(base_path, "p4"), "wb")
    pickle.dump(p4, file_p4)
    file_p5 = open(os.path.join(base_path, "p5"), "wb")
    pickle.dump(p5, file_p5)
    file_p3 = open(os.path.join(base_path, "p3"), "wb")
    pickle.dump(p3, file_p3)
    file_p1 = open(os.path.join(base_path, "p1"), "wb")
    pickle.dump(p1, file_p1)

    return (city, class_dict)


def create_parser():
    desc = """Process BGP measurements"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "-m",
        dest="measurement",
        action="store",
        required=True,
        help="Name of target measurement",
    )
    return parser


def main():

    parser = create_parser()
    opts = parser.parse_args()

    with open("../config.json", "r") as config_fd:
        config = json.load(config_fd)

    traceroute_file = config[opts.measurement]["traceroute_file"]

    final_classification = defaultdict(dict)

    with open("../data/" + traceroute_file, "r") as trace_data:
        traceroutes = json.load(trace_data)

    locations = []
    for city in config[opts.measurement]["location"]:
        locations.append(
            (
                city,
                config[opts.measurement]["location"][city],
                config[opts.measurement]["bgpdump"],
                traceroutes,
            )
        )

    num_proc = MAX if len(locations) > MAX else len(locations)

    pool = Pool(processes=num_proc)
    results_iterator = list(pool.imap(classification, locations))

    pool.close()
    pool.join()

    for r in results_iterator:
        final_classification[r[0]] = r[1]

    fd_out = open(f"../dump/{opts.measurement}.json", "w")
    json.dump(final_classification, fd_out, indent=4)


if __name__ == "__main__":
    sys.exit(main())
