#!/usr/bin/env python3

import sys
import re
import json
import statistics 
import os.path

for file in sys.argv[1:]:
    f = open(file)
    s = f.read().strip()

    outdata = {}
    mainparts = s.split("------------------- cpurange ---------------------")
    headers = mainparts[0].split('\n')
    outdata["date"]         = headers[0]
    outdata["context_size"] = headers[1]
    #outdata["marker"]       = headers[2]
    outdata["param_size"]   = headers[3]
    outdata["model"]        = headers[4]
    
    #3600-4dimm-schedutil-1instance-30B-ctx-512-ggml-model-q4_0.bin
    
    
    filename_info = os.path.basename(file).split("-")
    outdata["ram_feeq"]         = filename_info[0]
    outdata["dimm_count"]       = filename_info[1]
    outdata["governer"]         = filename_info[2]
    outdata["concurrent_instance_count"]   = int(filename_info[3].replace("instance", ""))
    filename_param_size         = filename_info[4]
    filename_context_size       = filename_info[6]
    filename_model              = "-".join(filename_info[7:])[:-4]
    
    if filename_param_size != outdata["param_size"]:
        print("metadata mismatch between filename and content: param_size: ({} != {}). aborting!".format(filename_param_size, outdata["param_size"]))
        sys.exit(1)
        
    if filename_context_size != outdata["context_size"]:
        print("metadata mismatch between filename and content: context_size: ({} != {}). aborting!".format(filename_context_size, outdata["context_size"]))
        sys.exit(1)
        
    if filename_model != outdata["model"]:
        print("metadata mismatch between filename and content: model: ({} != {}). aborting!".format(filename_model, outdata["model"]))
        sys.exit(1)
    
    
    if True:
        cpurange = mainparts[1].strip()
        #if cpurange == "": continue
        for runset in cpurange.split("------------------- 3RUN ---------------------"):
            
            entry = json.loads(json.dumps(outdata))
            entry["load_time"] = []
            entry["sample_time"] = []
            entry["prompt_eval_time"] = []
            entry["eval_time"] = []
            entry["total_time"] = []
            entry["threads"] = None
            
            runset = runset.strip()
            if runset == "": continue
            for run in runset.split("------------------- RUN ---------------------"):
                run = run.strip()
                if run == "": continue
                lineno = -1
                for line in run.split("\n"):
                    lineno += 1
                    line = line.strip()
                    if line == "": continue
                    
                    if lineno == 0:
                        cmd = line.split()
                        cmd = [s for s in cmd if cmd != ""]
                        entry["threads"] = int(cmd[3])
                        reported_model = os.path.basename(cmd[5])
                        if reported_model != entry["model"]:
                            print("metadata mismatch between filename and reported model: ({}, {}). aborting!".format(reported_model, entry["model"]))
                            sys.exit(1)
                    
                    prefix = "llama_model_load_internal: n_ctx      = "
                    if line.startswith(prefix):
                        entry["context"] = int(line[len(prefix):].strip())
                    
                    prefix = "llama_print_timings:"
                    if line.startswith(prefix):
                        timings = line[len(prefix):].strip()
                        #print(timings)
                        
                        if timings.startswith("load time ="):
                             entry["load_time"] += [ float(re.search('load time *= *([0-9.]*) *ms', timings).group(1)) ]
                        
                        elif timings.startswith("sample time ="):
                            entry["sample_time"] += [ float(re.search('sample time *=.*\( *([0-9.]*) *ms per token\)', timings).group(1)) ]
                    
                        elif timings.startswith("prompt eval time ="):
                            entry["prompt_eval_time"] += [ float(re.search('prompt eval time *=.*\( *([0-9.]*) *ms per token\)', timings).group(1)) ]
                            
                        elif timings.startswith("eval time ="):
                            entry["eval_time"] += [ float(re.search('eval time *=.*\( *([0-9.]*) *ms per token\)', timings).group(1)) ]
                        
                        elif timings.startswith("total time ="):
                             entry["total_time"] += [ float(re.search('total time *= *([0-9.]*) *ms', timings).group(1)) ]
            
            
            if entry["load_time"]:
                def values_calc_info(entry, key):
                    entry[key+"_mean"]          = statistics.mean(entry[key])
                    entry[key+"_median"]        = statistics.median(entry[key])
                    entry[key+"_max"]           = max(entry[key])
                    entry[key+"_min"]           = min(entry[key])
                    
                values_calc_info(entry, "load_time")
                values_calc_info(entry, "sample_time")
                values_calc_info(entry, "prompt_eval_time")
                values_calc_info(entry, "eval_time")
                values_calc_info(entry, "total_time")


    
            outfilename = "data/stage-1/"+"-".join([
                entry["ram_feeq"], 
                entry["dimm_count"],
                entry["governer"],
                str(entry["concurrent_instance_count"]),
                entry["param_size"],
                entry["context_size"],
                str(entry["threads"]),
                entry["model"]
            ])+".json"
            
            print("generating '{}'...".format(outfilename))
            o = open(outfilename, "w")
            o.write(json.dumps(entry, indent=4))
            o.flush()
            o.close()
            
        



#print(json.dumps(outdata, indent=4))

