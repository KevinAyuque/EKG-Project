"""
Takes the raw inputs and transforms them to an array.
"""
import argparse
import base64
import binascii
import codecs
import json
import numpy as np
import os
import shutil
import struct

#import matplotlib.pyplot as plt

#%matplotlib inline

def contains(str1, str2):
    index_start = str1.find(str2)
    index_end = index_start + len(str2) -1
    if index_start < 0:
        return 0
    
    if index_start-1 >= 0:
        if str1[index_start-1] != ",":
            return 0
    
    if index_end + 1 < len(str1):
        if str1[index_end + 1] != ",":
            return 0
    return 1

def process(directory, objects_name_group, objects_name_exclude_group, output_dir, verbose):
    """
    Goes through all the files
    """
    files_name = os.listdir(directory)
    Y = np.zeros(len(files_name))
    out_was_modified = np.zeros(len(files_name))
    out_file_name = []
    print(len(files_name))
    for j in range(len(files_name)):
        file_name = directory+"/"+files_name[j] 
        data = json.load(open(file_name))
        
        
        ds = data['RestingECG']['Diagnosis']['CategoriesDiagnosis']
        try:
            # AND
            for i in range(len(objects_name_group)):
                flag = 1
                objects_name = objects_name_group[i]
                objects_name_exclude = objects_name_exclude_group[i]
                for and_object_name in objects_name:
                    # OR
                    or_flag = 0
                    for object_name in and_object_name:
                        if or_flag == 0:
                            or_flag = contains(ds, object_name)
                        else:
                            break
                    if or_flag == 0:
                        flag = 0
                        break
                # Exclude
                for object_name_exclude in objects_name_exclude:
                    if flag == 1:
                        flag = abs(1 - contains(ds, object_name_exclude))
                    else:
                        break
                if flag == 1:
                    Y[j] = i + 1
                    break
        except:
            "ERROR"
            pass
        if verbose:
            print(Y[j])
        was_modified = 0
        if data['RestingECG']['Diagnosis']['CategoriesDiagnosis'] != data['RestingECG']['Diagnosis']['CategoriesOriginal']:
            was_modified = 1
                    
        out_was_modified[j] = was_modified
        out_file_name.append(files_name[j])


    np.savetxt(output_dir+'/was_modified.txt', out_was_modified, fmt='%d')
    np.savetxt(output_dir+'/Y.txt', Y, fmt='%d')

    with open(output_dir+'/file_name.json', 'w') as f:
        f.write(json.dumps(files_name))

def main():
    """
    -v:
    directory: the directory of the raw input data
    lead: 0 is for shorter one, 1 for longer one
    """
    parser = argparse.ArgumentParser(description='Flags')
    parser.add_argument('-v', dest='verbose', action='store_true')
    parser.add_argument('directory')
    parser.add_argument('disease')
    args = parser.parse_args()

    PERI = [['200']]
    PERI_IGNORE = ['302,200','145,302,155,200,220']

    STE = [['330,160','330,161', '330,162', '330,163', '330,165', '330,166', '330,174']]
    STE_IGNORE = ['312,330']

    # [0] = SVT, [1] = with Aberrancy
    SVT = [['21','50,346','51,346','52','53','55'], ['86','100','101','102','104','105','106','349']]
    SVT_IGNORE = []

    VT = [['70','72','73']]
    VT_IGNORE = []

    data = []
    data_ignore = []
    other_objects = []
    output_dir = ""

    if args.disease == "ps":
        data = [PERI, STE]
        data_ignore = [PERI_IGNORE, STE_IGNORE]
        other_objects = STE
        output_dir = "out_PS"
    elif args.disease == "vts":
        data = [VT, SVT]
        data_ignore = [VT_IGNORE, SVT_IGNORE]
        other_objects = PERI
        output_dir = "out_VTSVT"
    else:
        return

    # Clear folder if exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # Add to folder
    process(args.directory, data, data_ignore, output_dir, args.verbose)

main()