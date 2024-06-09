from collections import defaultdict
import sys
import json
import lib
import datetime

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

def redefine_classification(dict_classification, city):
    dict_classification[city]["null"] = []
    dict_classification[city]["private"] = []

    city_classification = dict_classification[city]

    drop_invalid = []
    ignore_roa = []
    prefer_valid = []
    protected = []
    for asn in city_classification:
        if city_classification[asn] == "drop-invalid":
            drop_invalid.append(asn)
        if city_classification[asn] == "ignore-roa":
            ignore_roa.append(asn)
        if city_classification[asn] == "prefer-valid":
            prefer_valid.append(asn)
        if city_classification[asn] == "unknown-protected":
            protected.append(asn)
    return dict_classification, drop_invalid, ignore_roa, prefer_valid, protected

def main():
    # using arguments to specify the file
    if len(sys.argv) != 4:
        print("Usage: python3 process_traceroute_v1.py <classification_file> <measurement> <city>")
        sys.exit(1)

    classification_file = sys.argv[1]
    measurement = sys.argv[2]
    city = sys.argv[3]

    with open("../config.json", "r") as config_f:
        config = json.load(config_f)

    # time for mapping basing in the choosed city
    start_time = config[measurement][city]["start"]
    end_time = config[measurement][city]["end"]

    # traceroute for mapping
    if city in config[measurement]:
        if not "traceroute" in config[measurement]:
            print("Traceroute file not defined!")
            sys.exit(1)
        traceroute_file = config[measurement]["traceroute"]
    else:
        print("City not defined!")
        sys.exit(1)
    with open("../data/" + traceroute_file, "r") as trace_data:
        traceroutes = json.load(trace_data)
    mapping_asn_traces = defaultdict(list)
    for trace in traceroutes:
        if lib.is_timestamp_between(start_time , end_time, trace["endtime"]):
            mapping_asn_traces[trace["origin_asn"]].append(trace)
    for asn in mapping_asn_traces:
        mapping_asn_traces[asn] = sorted(mapping_asn_traces[asn], key=lambda x: x["endtime"])
        assert mapping_asn_traces[asn][0]["endtime"] <= mapping_asn_traces[asn][-1]["endtime"]

    # Load classification file
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    with open("../data/" + classification_file, "r") as class_data:
            classification = json.load(class_data)
    
    round = 1
    read = False
    while True:
        if read:
            with open("../dump/classification_" + city + date + ".json", "r") as classification_data:
                classification = json.load(classification_data)
        classification, drop_invalid, ignore_roa, prefer_valid, protected = redefine_classification(classification, city)

        # Define variables for calculate ASNs
        calc_ignore = 0
        calc_prefer = 0
        calc_protected = 0
        calc_drop = 0

        for asn in mapping_asn_traces:
            if str(asn) not in ignore_roa and str(asn) not in drop_invalid and str(asn) not in prefer_valid and str(asn) not in protected:
                if  in_list(asn, mapping_asn_traces, ignore_roa, "138.185.228.1") and \
                    assert_no_route(asn, mapping_asn_traces, "138.185.229.1") and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, "138.185.230.1") or in_list(asn, mapping_asn_traces, protected, "138.185.230.1"))and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, "138.185.231.1") or in_list(asn, mapping_asn_traces, protected, "138.185.231.1")): # or protected or prefer
                        classification[city][asn] = "drop-invalid"
                        calc_drop += 1
                elif in_list(asn, mapping_asn_traces, ignore_roa, "138.185.228.1") and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, "138.185.230.1") or in_list(asn, mapping_asn_traces, protected, "138.185.230.1")) and \
                    in_list(asn, mapping_asn_traces, ignore_roa, "138.185.229.1") and \
                    not in_list(asn, mapping_asn_traces, ignore_roa, "138.185.231.1") and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, "138.185.231.1") or in_list(asn, mapping_asn_traces, protected, "138.185.231.1")):
                        classification[city][asn] = "prefer-valid"
                        calc_prefer += 1
                elif in_list(asn, mapping_asn_traces, ignore_roa, "138.185.228.1") and \
                    in_list(asn, mapping_asn_traces, ignore_roa, "138.185.230.1") and \
                    in_list(asn, mapping_asn_traces, ignore_roa, "138.185.229.1") and \
                    not (in_list(asn, mapping_asn_traces, drop_invalid, "138.185.229.1") or in_list(asn, mapping_asn_traces, protected, "138.185.229.1")) and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, "138.185.231.1") or in_list(asn, mapping_asn_traces, protected, "138.185.231.1")): #or protected or prefer
                        classification[city][asn] = "ignore-roa"
                        calc_ignore += 1
                elif (in_list(asn, mapping_asn_traces, protected, "138.185.228.1") or in_list(asn, mapping_asn_traces, drop_invalid, "138.185.228.1")) and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, "138.185.230.1") or in_list(asn, mapping_asn_traces, protected, "138.185.230.1")) and \
                    assert_no_route(asn, mapping_asn_traces, "138.185.229.1") and \
                    (in_list(asn, mapping_asn_traces, drop_invalid, "138.185.231.1") or in_list(asn, mapping_asn_traces, protected, "138.185.231.1")):
                        classification[city][asn] = "unknown-protected"
                        calc_protected += 1

        # Break if no more classification
        if calc_ignore == 0 and calc_prefer == 0 and calc_protected == 0 and calc_drop == 0:
            print(f"No more classification for {city}!")
            break

        # Update json
        with open("../dump/classification_" + city + date + ".json", "w") as classification_data:
            json.dump(classification, classification_data, indent = 4)

        print(f"Round {round}")
        print(f"calc_prefer = {calc_prefer}")
        print(f"calc_ignore = {calc_ignore}")
        print(f"calc_protected = {calc_protected}")
        print(f"calc_drop = {calc_drop}\n")
        round += 1
        read = True

main()
