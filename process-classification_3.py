#!/usr/bin/env python3

import lib
from collections import defaultdict
import pickle
import sys
import os

INVALID_ORIGIN = '61574'
VALID_ORIGIN = '47065'


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


def neighbors_prefix_usage(asn_t, data, origin):
    for asn in data:
        if not data[asn]:
            continue
        for it in range(0, len(data[asn])):
            if not data[asn][it] or not data[asn][it].isdigit():
                continue
            if int(data[asn][it]) == int(asn_t):
                neighbor = data[asn][it+1]
                if not neighbor.isdigit():
                    break
                if data[neighbor] and int(data[neighbor][-1]) == int(origin):
                    return True
    return False

# checa se pelo menos um asn estejam em dada classificação
def assert_one_classification(asn_t, data, class_t, class_dict):
    for asn in data[asn_t]:
        if asn == asn_t:
            continue
        if asn not in class_dict:
            return False
        if class_dict[asn] in class_t:
            return True
    return False

# checa se  todos os asn estejam em dada classificação
def assert_all_classification(asn_t, data, class_t, class_dict):
    for asn in data[asn_t]:
        if asn == '47065' or asn == '61574':
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
        if rec["prefix"] == prefix:
            pfx_routes[rec["peer_asn"]] = rec["as-path"]
    return pfx_routes


def classification_phase1(asn_t, class_dict, new0, new1, new2, new3, old0):
    if not asn_t.isdigit():
        return

    if asn_t not in class_dict:
        #first phase

        if len(new0[asn_t]) > 0 and int(new0[asn_t][-1]) == 61574 and \
        len(new1[asn_t]) > 0 and int(new1[asn_t][-1]) == 61574 and \
        len(new2[asn_t]) > 0 and int(new2[asn_t][-1]) == 61574 and \
        len(new3[asn_t]) > 0 and int(new3[asn_t][-1]) == 47065 and \
        len(old0[asn_t]) > 0 and int(old0[asn_t][-1]) == 61574:
            class_dict[asn_t] = "ignore-roa"

        elif len(new0[asn_t]) > 0 and int(new0[asn_t][-1]) == 61574 and \
            len(new1[asn_t]) > 0 and int(new1[asn_t][-1]) == 61574 and \
            len(new2[asn_t]) > 0 and int(new2[asn_t][-1]) == 47065 and \
            len(new3[asn_t]) > 0 and int(new3[asn_t][-1]) == 47065 and \
            len(old0[asn_t]) > 0 and int(old0[asn_t][-1]) == 61574 and \
            new0[asn_t] == old0[asn_t]:
            class_dict[asn_t] = "prefer-valid"

        elif len(new0[asn_t]) > 0 and int(new0[asn_t][-1]) == 61574 and \
            len(new1[asn_t]) == 0 and \
            len(new2[asn_t]) > 0 and int(new2[asn_t][-1]) == 47065 and \
            len(new3[asn_t]) > 0 and int(new3[asn_t][-1]) == 47065 and \
            len(old0[asn_t]) > 0 and int(old0[asn_t][-1]) == 61574 and \
            new0[asn_t] == old0[asn_t]:
            class_dict[asn_t] = "drop-invalid"
        else:
            class_dict[asn_t] = "unknown"

def classification_phase2(asn_t, class_dict, new0, new1, new2, new3, old0):
    if not asn_t.isdigit():
        return

    # second phase
    if class_dict[asn_t] == "drop-invalid":
        if assert_one_classification(asn_t, new0, ["drop-invalid", "unknown"], class_dict):
            class_dict[asn_t] = "unknown"

    if class_dict[asn_t] == "ignore-roa":
        if assert_all_classification(asn_t, new3, ["drop-invalid", "prefer-valid"], class_dict) or \
            neighbors_prefix_usage(asn_t, new2, VALID_ORIGIN):
            class_dict[asn_t] = "ignore-roa"
        else:
            class_dict[asn_t] = "prefer-ignore"

    if class_dict[asn_t] == "prefer-valid":
        if assert_all_classification(asn_t, new1, ["ignore-roa"], class_dict) or \
            neighbors_prefix_usage(asn_t, new2, INVALID_ORIGIN):
            class_dict[asn_t] = "prefer-valid"
        else:
            class_dict[asn_t] = "prefer-ignore"


nicbr_dump = "bgpdump_2023-12-18T00:00:00.000000Z_2023-12-20T00:00:00.000000Z_updates_ripe_ris_roa.json"

new_p0 = get_records(nicbr_dump,"2023-12-18T19:30:00.000000Z", "2023-12-18T20:55:00.491672Z", "138.185.228.0/24")

new_p1 = get_records(nicbr_dump,"2023-12-18T19:30:00.000000Z", "2023-12-18T20:55:00.491672Z", "138.185.229.0/24")

new_p2 = get_records(nicbr_dump,"2023-12-18T19:30:00.000000Z", "2023-12-18T20:55:00.491672Z", "138.185.230.0/24")

new_p3 = get_records(nicbr_dump,"2023-12-18T19:30:00.000000Z", "2023-12-18T20:55:00.491672Z", "138.185.231.0/24")

new_p0 = complete_routes(new_p0)
new_p1 = complete_routes(new_p1)
new_p2 = complete_routes(new_p2)
new_p3 = complete_routes(new_p3)


arin_dump = "bgpdump_2023-12-18T00:00:00.000000Z_2023-12-20T00:00:00.000000Z_updates_ripe_ris_no_roa.json"

old_p0 = get_records(arin_dump,"2023-12-18T19:30:00.000000Z", "2023-12-18T20:55:00.491672Z", "204.9.170.0/24")

old_p0 = complete_routes(old_p0)


as_list = []
for d in [new_p0, new_p1, new_p2, new_p3, old_p0]:
    for key in d:
        if key not in as_list:
            as_list.append(key)

new_p0, max_p0 = parse_routes(new_p0, as_list)
new_p1, max_p1 = parse_routes(new_p1, as_list)
new_p2, max_p2 = parse_routes(new_p2, as_list)
new_p3, max_p3 = parse_routes(new_p3, as_list)
old_p0, old_max_p0 = parse_routes(old_p0, as_list)

max = max([max_p0, max_p1, max_p2, max_p3, old_max_p0])

class_dict = {}

#casos base
class_dict["47065"] = "ignore-roa"
class_dict["61574"] = "ignore-roa"
class_dict["20473"] = "drop-invalid"

#first phase
for i in range(max-1, -1, -1):
    for asn in new_p0:
        if len(new_p0[asn]) > i:
            classification_phase1(new_p0[asn][i], class_dict, new_p0, new_p1, new_p2, new_p3, old_p0)
        if len(new_p1[asn]) > i:
            classification_phase1(new_p1[asn][i], class_dict, new_p0, new_p1, new_p2, new_p3, old_p0)
        if len(new_p2[asn]) > i:
            classification_phase1(new_p2[asn][i], class_dict, new_p0, new_p1, new_p2, new_p3, old_p0)
        if len(new_p3[asn]) > i:
            classification_phase1(new_p3[asn][i], class_dict, new_p0, new_p1, new_p2, new_p3, old_p0)

for i in range(max-1, -1, -1):
    #second_phase
    for asn in new_p0:
        if len(new_p0[asn]) > i:
            classification_phase2(new_p0[asn][i], class_dict, new_p0, new_p1, new_p2, new_p3, old_p0)
        if len(new_p1[asn]) > i:
            classification_phase2(new_p1[asn][i], class_dict, new_p0, new_p1, new_p2, new_p3, old_p0)
        if len(new_p2[asn]) > i:
            classification_phase2(new_p2[asn][i], class_dict, new_p0, new_p1, new_p2, new_p3, old_p0)
        if len(new_p3[asn]) > i:
            classification_phase2(new_p3[asn][i], class_dict, new_p0, new_p1, new_p2, new_p3, old_p0)



if len(sys.argv) == 2:
    location = sys.argv[1]

    file = open(os.path.join(location, "classification"), 'wb')
    pickle.dump(class_dict, file)

    file_new_p0 = open(os.path.join(location, "new_p0"), 'wb')
    pickle.dump(new_p0, file_new_p0)
    file_new_p1 = open(os.path.join(location, "new_p1"), 'wb')
    pickle.dump(new_p1, file_new_p1)
    file_new_p2 = open(os.path.join(location, "new_p2"), 'wb')
    pickle.dump(new_p2, file_new_p2)
    file_new_p3 = open(os.path.join(location, "new_p3"), 'wb')
    pickle.dump(new_p3, file_new_p3)
    file_old_p0 = open(os.path.join(location, "old_p0"), 'wb')
    pickle.dump(old_p0, file_old_p0)
else:
    print("usage: process_classification.py [location] [folder_name]")
