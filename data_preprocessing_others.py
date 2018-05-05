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

def output_leads(directory, files_name, out_dir, verbose):
    """
    Goes through all the files
    """
    #files_name = os.listdir(directory)
    #files_name = [x for x in files_name if x not in fi]
    out_file_name = []
    for j in range(len(files_name)):
        file_name = directory+"/"+files_name[j] 
        data = json.load(open(file_name))

        out_file_name.append(files_name[j])
        for i, waveform in enumerate(data['RestingECG']['Waveform']):
            leads = get_leads(waveform)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            np.savetxt(out_dir+'/'+str(i)+"_"+(str(j).zfill(4))+'.txt', leads, fmt='%d')


    with open(out_dir+'/file_name.json', 'w') as f:
        f.write(json.dumps(out_file_name))

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
    parser.add_argument('ignore1')
    parser.add_argument('ignore2')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    # Clear folder if exists
    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)

    # Add to folder

    files_name = os.listdir(args.directory)
    print(len(files_name))

    ignore1 = []
    with open(args.ignore1+'/file_name.json', 'r') as f:
        ignore1 = json.loads(f.read())
    
    #print(ignore1)
    files_name = [x for x in files_name if x not in ignore1]
    print(len(files_name))

    ignore2 = []
    with open(args.ignore2+'/file_name.json', 'r') as f:
        ignore2 = json.loads(f.read())

    files_name = [x for x in files_name if x not in ignore2]
    print(len(files_name))
    #files_name = [x for x in files_name if x not in fi]
    

    output_leads(args.directory, files_name, args.output_dir, args.verbose)

main()