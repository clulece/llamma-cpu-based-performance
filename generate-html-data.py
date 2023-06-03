#!/usr/bin/env python3

import sys
import re
import json
import statistics 
import os.path
import collections

data = []

for file in os.listdir("data/stage-1"):
    data += [ [ ("data/stage-1/" + file), json.loads(open("data/stage-1/" + file).read()) ] ]

x_key = 'threads'
#exclusive_filters = [ (x[1:]).split("=", 1) for x in sys.argv[3:] if x.startswith("!") ] 
#inclusive_filters = [ x.split("=", 1)   for x in sys.argv[3:] if not x.startswith("!") ] 
exclusive_filters = []
inclusive_filters = []

print("Exclusive_filters: {}".format(exclusive_filters), file=sys.stderr)
print("Inclusive_filters: {}".format(inclusive_filters), file=sys.stderr)

selected_data = []

for d in data:
    #print(json.dumps(data))
    
    exclude_flag = False
    for f in exclusive_filters:
        exclude_flag |= (d[1][f[0]] == f[1])
    if exclude_flag: continue
    
    if len(inclusive_filters) > 0:
        not_included = False
        for f in inclusive_filters:
            not_included |= not (d[1][f[0]] == f[1])
        if not_included: continue
    
    print("selecting '{}'".format(d[0]), file=sys.stderr)
    selected_data += [d[1]]


def uniq(l):
    m = []
    for i in l:
        if len(m) > 0 and m[-1] == i: 
            continue
        else:
            m += [i]
    return m

def entry_name(entry):
    return "-".join([
                entry["ram_feeq"], 
                entry["dimm_count"],
                entry["governer"],
                str(entry["concurrent_instance_count"]),
                entry["param_size"],
                entry["context_size"],
                str(entry["threads"]),
                entry["model"]
            ])
            
def entry_name_without_threads(entry):
    return "-".join([
                entry["ram_feeq"], 
                entry["dimm_count"],
                entry["governer"],
                str(entry["concurrent_instance_count"]),
                entry["param_size"],
                entry["context_size"],
                entry["model"]
            ])

selected_data = sorted(selected_data, key=lambda x: "{:050d}".format(x[x_key])+entry_name(x))
ordered_x_values = uniq([l[x_key] for l in selected_data])

#row_length = len(selected_data)/len(ordered_x_values)
#if row_length != int(row_length):
#    print("row data is not perfectly tabular, may contain holes or intermediary values: {} and {}".format(len(selected_data), len(ordered_x_values)))
#    sys.exit(1)


#for d in selected_data:
#    print(entry_name(d), file=sys.stderr)


#print(json.dumps(selected_data))

headers = set()
for data in selected_data:
    headers.add(entry_name_without_threads(data))

timings = [ 
    "load_time_median", 
    "sample_time_median", 
    "prompt_eval_time_median",
    "eval_time_median",
    "total_time_median"
]

curves_sets = {}    
for timing_table in timings: 
    curves_set = {}
    for entry in selected_data:
        unified_name = entry_name_without_threads(entry)
        
        if unified_name not in curves_set:
            curves_set[unified_name] = {
                "mode": 'lines+markers',
                #"visible": False,
                "name": unified_name
            }
            
        curves_set[unified_name]["x"] = curves_set[unified_name].get("x", []) + [entry[x_key]]
        curves_set[unified_name]["y"] = curves_set[unified_name].get("y", []) + [entry[timing_table]]
        
    curves_sets[timing_table] = []
    for key, value in curves_set.items():
        curves_sets[timing_table] += [ value ]

open("data/html-data/data.json", "w").write(json.dumps(curves_sets, indent=4))
