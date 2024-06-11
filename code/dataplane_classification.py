from collections import defaultdict, Counter
import sys
import json
import lib
import argparse

def in_list(trace, target_list):
    if len(trace["result"]) >= 2:
        if str(trace["result"][1]) in target_list:
            return True
    return False

def assert_no_route(trace):
    if len(trace["result"]) < 2:
        return False
    for i in range(1, len(trace["result"])):
        if str(trace["result"][i]).isdigit():
            return False
    return True

def origin(trace, origin):
    if trace["result"] >= 2:
        if trace["result"][-1] == origin or trace["result"][-2] == origin:
            return True
    return False

def get_last_classification(dict_classification, city):

    drop_invalid = []
    ignore_roa = []
    prefer_valid = []
    protected = []

    for asn in dict_classification[city]:
        if not asn.isdigit():
            continue
        if dict_classification[city][asn] == "drop-invalid":
            drop_invalid.append(str(asn))
        if dict_classification[city][asn] == "ignore-roa":
            ignore_roa.append(str(asn))
        if dict_classification[city][asn] == "prefer-valid":
            prefer_valid.append(str(asn))
        if dict_classification[city][asn] == "unknown-protected":
            protected.append(str(asn))
    return drop_invalid, ignore_roa, prefer_valid, protected


def get_stable_trace(asn_traceroute_list, threshold=2):
    trace_list = [(trace["dst_addr"], tuple(trace['result'])) for trace in asn_traceroute_list]
    counter = Counter(trace_list)
    most_common_trace, count = counter.most_common(1)[0]
    if count < threshold or len(most_common_trace[1]) < 2:
        return None
    return (most_common_trace[0], list(most_common_trace[1]))

def get_last_trace(asn_tracerout_list):
    return asn_tracerout_list[-1]

def create_parser():
    desc = """Process traceroute measurements"""
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

    P2 = "138.185.228.1"
    P3 = "138.185.231.1"
    P4 = "138.185.229.1"
    P5 = "138.185.230.1"

    parser = create_parser()
    opts = parser.parse_args()

    with open("../config.json", "r") as config_f:
        config = json.load(config_f)

    # time of the measurement according to the location
    start_time = config[opts.measurement]["location"][opts.city]["start"]
    end_time = config[opts.measurement]["location"][opts.city]["end"]
    traceroute_file = config[opts.measurement]["traceroute_file"]

    with open("../data/" + traceroute_file, "r") as trace_data:
        traceroutes = json.load(trace_data)

    asn_list = []
    # get all traceroutes by ASN
    mapping_asn_traces = defaultdict(list)
    for trace in traceroutes:
        if lib.is_timestamp_between(start_time , end_time, trace["endtime"]):
            mapping_asn_traces[(str(trace["origin_asn"]),trace["dst_addr"])].append(trace)
            asn_list.append(str(trace["origin_asn"]))

    # get most stable tracerout by ASN
    asn_trace = {}
    for asn_dst in mapping_asn_traces:
        asn_trace[asn_dst] = get_last_trace(mapping_asn_traces[asn_dst])

    with open("../data/classification_%s.json" % opts.measurement, "r") as classification_fd:
        classification = json.load(classification_fd)


    drop_invalid, ignore_roa, prefer_valid, protected = get_last_classification(classification, opts.city)
    classification[opts.city]["null"] = []
    classification[opts.city]["private"] = []

    round = 1
    while True:

        calc_ignore = 0
        calc_prefer = 0
        calc_protected = 0
        calc_drop = 0

        for asn in asn_list:
            if asn not in ignore_roa and asn not in drop_invalid and asn not in prefer_valid and asn not in protected:
                if (not (asn,P2) in asn_trace) or (not (asn,P3) in asn_trace) or (not (asn,P5) in asn_trace) or (not (asn,P4) in asn_trace):
                    continue
                if  in_list(asn_trace[(asn,P2)], ignore_roa) and \
                    assert_no_route(asn_trace[(asn,P4)]) and \
                    (in_list(asn_trace[(asn,P5)], drop_invalid) or in_list(asn_trace[(asn,P5)], protected)) and \
                    (in_list(asn_trace[(asn,P3)], drop_invalid) or in_list(asn_trace[(asn,P3)], protected)):
                        classification[opts.city][str(asn)] = "drop-invalid"
                        calc_drop += 1
                elif (in_list(asn_trace[(asn,P5)], drop_invalid) or in_list(asn_trace[(asn,P5)], protected)) and \
                    in_list(asn_trace[(asn,P4)], ignore_roa) and \
                    (in_list(asn_trace[(asn,P3)], drop_invalid) or in_list(asn_trace[(asn,P3)], protected)): # missing P2 classification
                        classification[opts.city][str(asn)] = "prefer-valid"
                        calc_prefer += 1
                elif in_list(asn_trace[(asn,P5)], ignore_roa) and \
                    in_list(asn_trace[(asn,P4)], ignore_roa) and \
                    (in_list(asn_trace[(asn,P3)], drop_invalid) or in_list(asn_trace[(asn,P3)], protected)): # missing P2 classification
                        classification[opts.city][str(asn)] = "ignore-roa"
                        calc_ignore += 1
                elif (in_list(asn_trace[(asn,P2)], protected) or in_list(asn_trace[(asn,P2)], drop_invalid)) and \
                    (in_list(asn_trace[(asn,P5)], drop_invalid) or in_list(asn_trace[(asn,P5)], protected)) and \
                    assert_no_route(asn_trace[(asn,P4)]) and \
                    (in_list(asn_trace[(asn,P3)], drop_invalid) or in_list(asn_trace[(asn,P3)], protected)):
                        classification[opts.city][str(asn)] = "unknown-protected"
                        calc_protected += 1


        print(f"Round {round}")
        print(f"calc_prefer = {calc_prefer}")
        print(f"calc_ignore = {calc_ignore}")
        print(f"calc_protected = {calc_protected}")
        print(f"calc_drop = {calc_drop}\n")

        # Break if no more classification
        if calc_drop + calc_prefer + calc_ignore + calc_protected == 0:
            print(f"No more classification for {opts.city}!")
            break
        round += 1

        drop_invalid, ignore_roa, prefer_valid, protected = get_last_classification(classification, opts.city)

    with open("../dump/classification_%s.json" %  opts.measurement, "w") as classification_fd_out:
        json.dump(classification, classification_fd_out, indent = 4)

if __name__ == "__main__":
    sys.exit(main())
