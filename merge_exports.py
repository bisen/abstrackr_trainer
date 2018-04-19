import csv
import sys
import os
import fnmatch
import operator
from collections import defaultdict

def merge_exports(p_id):
    iters = 50    
    
    a_array = []
    for _ in range(iters):
        a_array.append([])

    to_write = []
    firstfile = True
    a_dict = {}
    for filename in os.listdir('.'):
        print filename
        if fnmatch.fnmatch(filename,"predictions_"+str(p_id)+"_*_*.csv"):
            n_parts = filename.split("_")
            inc_i = int(n_parts[2])
            iter_i = int(n_parts[4].replace(".csv",""))
            f = open(filename, 'r')
            reader = csv.reader(f, delimiter=',', quotechar='"')
            _pass = True
            raw_data = []
            d_dict = defaultdict(list)
            for row in reader:
                if len(row) < 2:
                    break
                if _pass:
                    _pass = False
                    continue
                raw_data.append(row)
                d_dict[row[1]] = row
            sortedlist = sorted(raw_data, key=operator.itemgetter(1)) 
            a_array[iter_i].append((inc_i, d_dict))
        
    iter_count = 0    
    for iter_arr in a_array:
        sortedlist = sorted(iter_arr, key=operator.itemgetter(0))
        _pass = True
        to_write = {}
        header = ["id","title"]
        ggg = 0
        for _, inc_dict in sortedlist:
            if len(inc_dict) == 0:
                continue
            header += ["prob_"+str(ggg),"pred_"+str(ggg), "group_"+str(ggg)]
            ggg += 1
            if _pass:
                _pass = False
                to_write = inc_dict
                for key in inc_dict.keys():
                continue
            for key in inc_dict.keys():
                if key == "True":
                    print "NASIL!?"
                to_write[key] += inc_dict[key][2:]
        print "bas"
        final_arr = sorted(to_write.values(), key=operator.itemgetter(1))
        fname = "project_"+str(p_id)+"_iter_"+str(iter_count)+".csv"
        fout = open(fname, 'w+')
        writer = csv.writer(fout)
        writer.writerow(header)
        print "son"
        for f_row in final_arr:
            writer.writerow(f_row)
        iter_count += 1 
merge_exports(int(sys.argv[1])) 

