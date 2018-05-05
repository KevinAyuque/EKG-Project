"""
Transforms the inputs file into a single file for training and testing.
"""
import argparse
import json
import numpy as np
import os
import shutil

def main():
    parser = argparse.ArgumentParser(description='Flags')
    parser.add_argument('-v', dest='verbose', action='store_true')
    parser.add_argument('-s', dest='split', action='store_true')
    parser.add_argument('directory1')
    parser.add_argument('directory2')
    parser.add_argument('outdir_name')
    parser.add_argument('test_percentage', type=float)
    parser.add_argument('nlead')
    args = parser.parse_args()

    if args.test_percentage > 1 or args.test_percentage < 0:
        return
    
    #print("ASD")
    outdir = "data_"
    outdir += args.outdir_name
    if args.nlead == '0':
        outdir += "_300"
    elif args.nlead == '1':
        outdir += "_2500"
    else:
        return

    #print(outdir)

    cat_dirs = [args.directory1, args.directory2]

    X = []
    Y = []
    M = []
    
    current_y = -1
    for cat_dir in cat_dirs:
        #print(cat_dir)
        with open(cat_dir+'/was_modified.json', 'r') as f:

            M_temp = json.loads(f.read())
            M.extend(M_temp)

        current_y += 1
        files = os.listdir(cat_dir)
        files.sort()

        #print(len(files))
        n_files = 0
        for a_file in files:
            # 0 or 1
            if a_file[0] == args.nlead:
                n_files += 1
                if args.verbose:
                    print(a_file)
                a_data = np.loadtxt(cat_dir+"/"+a_file)
                X.append(a_data)
                Y.append(current_y)
        #print(n_files)

    nTest = round(len(X)*args.test_percentage)

    print("TOTAL ",len(X))
    print("TOTAL TEST ",nTest)
    print("TOTAL TRAINING ",len(X) - nTest)

    #print(M)
    #print(sum(M))

    s = np.arange(0, len(X), 1)
    np.random.shuffle(s)

    X_np = np.array(X)
    Y_np = np.array(Y)
    M_np = np.array(M)
    X_np = X_np[s]
    Y_np = Y_np[s]
    M_np = M_np[s]

    if args.split:
        outdir += '_split'

    if os.path.exists(outdir):
        shutil.rmtree(outdir)

    os.makedirs(outdir)

    if args.split:
        np.save(outdir+'/X_test', X_np[:nTest])
        np.save(outdir+'/X_train', X_np[nTest:])
        np.save(outdir+'/Y_test', Y_np[:nTest])
        np.save(outdir+'/Y_train', Y_np[nTest:])
        np.save(outdir+'/M_test', M_np[:nTest])
        np.save(outdir+'/M_train', M_np[nTest:])
        np.save(outdir+'/r_test', s[:nTest])
        np.save(outdir+'/r_train', s[nTest:])
    else:
        np.save(outdir+'/X', X_np)
        np.save(outdir+'/Y', Y_np)
        np.save(outdir+'/M', M_np)
        np.save(outdir+'/r', s)

main()