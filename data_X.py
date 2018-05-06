"""
Creates the array of waveforms for Y.
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
    leads = np.zeros([8, total])
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
            leads[2] = cleaned_data #6
        if lead["LeadID"] == "V2":
            leads[3] = cleaned_data #7
        if lead["LeadID"] == "V3":
            leads[4] = cleaned_data #8
        if lead["LeadID"] == "V4":
            leads[5] = cleaned_data #9
        if lead["LeadID"] == "V5":
            leads[6] = cleaned_data #10
        if lead["LeadID"] == "V6":
            leads[7] = cleaned_data #11

    #leads[2] = leads[1] - leads[0]
    #leads[3] = -(leads[0] + leads[1])/2
    #leads[4] = leads[0] - leads[1]/2
    #leads[5] = leads[1] - leads[0]/2
    return leads

def output_leads(outdir, directory, size, verbose):
    """
    Goes through all the files
    """

    files_name = json.load(open(directory+"/file_name.json"))

    X = []

    for j in range(len(files_name)):
        if verbose:
            print(j)
        file_name = outdir+"/"+files_name[j] 
        data = json.load(open(file_name))
        waveform = data['RestingECG']['Waveform'][size]
        leads = get_leads(waveform)
        X.append(leads)
    X_np = np.array(X)
    return X_np



def main():
    parser = argparse.ArgumentParser(description='Flags')
    parser.add_argument('-v', dest='verbose', action='store_true')
    parser.add_argument('directory')
    parser.add_argument('outdir')
    parser.add_argument('size', type = int)
    args = parser.parse_args()

    if args.size == 0:
        outdir = args.directory + "/X_300"
    elif args.size == 1:
        outdir = args.directory + "/X_2500"
    else:
        return

    X = output_leads(args.outdir, args.directory, args.size, args.verbose)
    np.save(outdir, X)



main()