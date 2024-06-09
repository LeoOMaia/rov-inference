from collections import defaultdict
import sys
import json
import lib
import argparse

def in_list(asn, mapping_asn_traces, target_list, dst_ip):
    for trace in mapping_asn_traces[asn]:
        if len(trace["result"]) > 1:
            if trace["dst_addr"] == dst_ip and \
                str(trace["result"][1]) in target_list:
                return True
    return False

def assert_no_route(asn, mapping_asn_traces, dst_ip):
    for trace in mapping_asn_traces[asn]:
        if len(trace["result"]) > 1:
            if trace["dst_addr"] == dst_ip:
                for i in range(1, len(trace["result"])):
                    if str(trace["result"][i]).isdigit():
                        return False
    return True

def get_last_classification(dict_classification, city):

    drop_invalid = []
    ignore_roa = []
    prefer_valid = []
    protected = []

    for asn in dict_classification[city]:
        if dict_classification[city][asn] == "drop-invalid":
            drop_invalid.append(str(asn))
        if dict_classification[city][asn] == "ignore-roa":
            ignore_roa.append(str(asn))
        if dict_classification[city][asn] == "prefer-valid":
            prefer_valid.append(str(asn))
        if dict_classification[city][asn] == "unknown-protected":
            protected.append(str(asn))
    return drop_invalid, ignore_roa, prefer_valid, protected

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

    # time for mapping basing in the choosed city
    start_time = config[opts.measurement]["location"][opts.city]["start"]
    end_time = config[opts.measurement]["location"][opts.city]["end"]
    traceroute_file = config[opts.measurement]["traceroute_file"]

    with open("../data/" + traceroute_file, "r") as trace_data:
        traceroutes = json.load(trace_data)

    mapping_asn_traces = defaultdict(list)
    for trace in traceroutes:
        if lib.is_timestamp_between(start_time , end_time, trace["endtime"]):
            mapping_asn_traces[trace["origin_asn"]].append(trace)

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

        for asn in mapping_asn_traces:
            if str(asn) not in ignore_roa and str(asn) not in drop_invalid and str(asn) not in prefer_valid and str(asn) not in protected:
                if  in_list(asn, mapping_asn_traces, ignore_roa, P2) and \
                    assert_no_route(asn, mapping_asn_traces, P4) and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, P5) or in_list(asn, mapping_asn_traces, protected, P5))and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, P3) or in_list(asn, mapping_asn_traces, protected, P3)):
                        classification[opts.city][str(asn)] = "drop-invalid"
                        calc_drop += 1
                elif in_list(asn, mapping_asn_traces, ignore_roa, P2) and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, P5) or in_list(asn, mapping_asn_traces, protected, P5)) and \
                    in_list(asn, mapping_asn_traces, ignore_roa, P4) and \
                    not in_list(asn, mapping_asn_traces, ignore_roa, P3) and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, P3) or in_list(asn, mapping_asn_traces, protected, P3)):
                        classification[opts.city][str(asn)] = "prefer-valid"
                        calc_prefer += 1
                elif in_list(asn, mapping_asn_traces, ignore_roa, P2) and \
                    in_list(asn, mapping_asn_traces, ignore_roa, P5) and \
                    in_list(asn, mapping_asn_traces, ignore_roa, P4) and \
                    not (in_list(asn, mapping_asn_traces, drop_invalid, P4) or in_list(asn, mapping_asn_traces, protected, P4)) and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, P3) or in_list(asn, mapping_asn_traces, protected, P3)): #or protected or prefer
                        classification[opts.city][str(asn)] = "ignore-roa"
                        calc_ignore += 1
                elif (in_list(asn, mapping_asn_traces, protected, P2) or in_list(asn, mapping_asn_traces, drop_invalid, P2)) and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, P5) or in_list(asn, mapping_asn_traces, protected, P5)) and \
                    assert_no_route(asn, mapping_asn_traces, P4) and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, P3) or in_list(asn, mapping_asn_traces, protected, P3)):
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
