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

def decode_string(coded_string, amplitude):
    """
    Decodes the encoded data in the 64Base encoding
    """
    decoded_data = base64.b64decode(coded_string)
    cleaned_data = struct.unpack('<' + 'h' * (len(decoded_data)//2) , decoded_data)
    return map(lambda x: x * amplitude, cleaned_data)

def plot_lead(decoded_data):
    """
    Plots the decoded data
    """
    f, ax = plt.subplots()
    ax.plot(decoded_data)

def get_leads(waveform):
    """Gets the leads on a waveform. Some leads are reconstructed based on "Medical Data Storage, Visualization and Interpretation: A Case Study Using a Proprietary ECG XML Format"
    """
    ref_total = int(waveform['LeadData'][0]['LeadSampleCountTotal'])
    total = ref_total
    if ref_total == 600 or ref_total == 5000:
        total = int(ref_total/2)
    leads = np.zeros([12, total])
    for lead in waveform['LeadData']:
        amplitude = float(lead['LeadAmplitudeUnitsPerBit'])
        cleaned_data = decode_string(lead['WaveFormData'],amplitude)
        
        if ref_total == 600 or ref_total == 5000 :
            cleaned_data = [(a + b) / 2 for a, b in zip(cleaned_data[::2], cleaned_data[1::2])]

        if lead["LeadID"] == "I":
            leads[0] = cleaned_data
        if lead["LeadID"] == "II":
            leads[1] = cleaned_data
        if lead["LeadID"] == "V1":
            leads[6] = cleaned_data
        if lead["LeadID"] == "V2":
            leads[7] = cleaned_data
        if lead["LeadID"] == "V3":
            leads[8] = cleaned_data
        if lead["LeadID"] == "V4":
            leads[9] = cleaned_data
        if lead["LeadID"] == "V5":
            leads[10] = cleaned_data
        if lead["LeadID"] == "V6":
            leads[11] = cleaned_data

    leads[2] = leads[1] - leads[0]
    leads[3] = -(leads[0] + leads[1])/2
    leads[4] = leads[0] - leads[1]/2
    leads[5] = leads[1] - leads[0]/2
    return leads

def contains(str1, str2):
    #print(str1, str2)
    index_start = str1.find(str2)
    index_end = index_start + len(str2) -1
    if index_start < 0:
        return 0
    
    if index_start-1 >= 0:
    #    print(str1[index_start - 1])
        if str1[index_start-1] != ",":
            return 0
    
    if index_end + 1 < len(str1):
    #    print(str1[index_end + 1])
        if str1[index_end + 1] != ",":
            return 0
    return 1
#str1.find(str2)

def output_leads(directory, objects_name, objects_name_exclude, other_objects, other_objects_exclude, out_dir, flag_out, verbose):
    """
    Goes through all the files
    """
    files_name = os.listdir(directory)
    out_was_modified = []
    out_file_name = []
    counter = 0
    for j in range(len(files_name)):
        file_name = directory+"/"+files_name[j] 
        data = json.load(open(file_name))
        
        flag = 1
        ds = data['RestingECG']['Diagnosis']['CategoriesDiagnosis']
        try:
            # AND
            for and_object_name in objects_name:
                # OR
                or_flag = 0
                for object_name in and_object_name:
                    if or_flag == 0:
                        or_flag = contains(ds, object_name)
                    else:
                        break
                        #print(or_flag)
                    #if object_name in ds #.split(','):
                    #    or_flag = 1
                    #    #break
                if or_flag == 0:
                    flag = 0
                    break
            # Exclude
            for object_name_exclude in objects_name_exclude:
                if flag == 1:
                    flag = abs(1 - contains(ds, object_name_exclude))
                else:
                    break
                #if object_name_exclude in ds.split(','):
                #    flag = 0
                #    break
        except:
            pass
        if flag == 1:
            print(ds)
            counter += 1
            if verbose:
                print(file_name)
            for ds in data['RestingECG']['Diagnosis']['DiagnosisStatement']:
                if verbose:
                    print(ds['StmtText'])
            if flag_out:
                was_modified = 0
                if data['RestingECG']['Diagnosis']['CategoriesDiagnosis'] != data['RestingECG']['Diagnosis']['CategoriesOriginal']:
                    was_modified = 1
                    for and_object_name in other_objects:
                        or_modified = 0
                        for or_object_name in and_object_name:
                            if or_object_name in data['RestingECG']['Diagnosis']['CategoriesOriginal']:
                                or_modified = 1
                    if or_modified == 0:
                        was_modified = 0
                    
                out_was_modified.append(was_modified)
                out_file_name.append(files_name[j])
                for i, waveform in enumerate(data['RestingECG']['Waveform']):
                    leads = get_leads(waveform)
                    if not os.path.exists(out_dir):
                        os.makedirs(out_dir)
                    np.savetxt(out_dir+'/'+str(i)+"_"+(str(counter-1).zfill(4))+'.txt', leads, fmt='%d')

    with open(out_dir+'/was_modified.json', 'w') as f:
        f.write(json.dumps(out_was_modified))

    with open(out_dir+'/file_name.json', 'w') as f:
        f.write(json.dumps(out_file_name))

    print(len(out_was_modified))
    print(len(out_file_name))
    print("TOTAL",counter)

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

    if args.disease == "p":
        data = PERI
        data_ignore = PERI_IGNORE
        other_objects = STE
        output_dir = "out_PERICARDITIS"
    elif args.disease == "s":
        data = STE
        data_ignore = STE_IGNORE
        other_objects = PERI
        output_dir = "out_STEMI"
    elif args.disease == "v":
        data = VT
        data_ignore = VT_IGNORE
        other_objects = SVT
        output_dir = "out_VT"
    elif args.disease == "sv":
        data = SVT
        data_ignore = SVT_IGNORE
        other_objects = VT
        output_dir = "out_SVT"
    else:
        return

    #print(data)

    # Clear folder if exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Add to folder
    output_leads(args.directory, data, data_ignore, other_objects, [], output_dir, True, args.verbose)

main()