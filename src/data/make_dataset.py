from __future__ import print_function
import sys, os, pandas as pd, geocoder, pdb 

sys.path.insert(0, os.environ['PROJECT_PATH']) 

from config.resources import data_paths
#  from src.data.helper_utils.msa_data_builder import get_mean_coords

def build_msa_coords_df(path_to_file):
    msa_coords_df = pd.DataFrame(columns=('Code', 'Name', 'Coords'))
    msa_codes_df = pd.read_csv(path_to_file, header=[0,1] )
    for index, row in msa_codes_df.iterrows():
        msa_code, msa_name = row['metdiv'], row['mdivname']
        msa_coords = geocoder.google(msa_name).latlng
        msa_coords_df.loc[index] = [msa_code, msa_name, msa_coords]
    print("\nSample Data:\n", msa_coords_df.head())
    print("\nWriting data to " + data_paths['msa_coords'])
    msa_coords_df.to_csv(data_paths['msa_coords'], index=False, encoding='latin1')

if __name__ == '__main__':
    path_to_msa_codes = data_paths['msa_codes'] 
    build_msa_coords_df(path_to_msa_codes)
