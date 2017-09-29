from __future__ import print_function

import requests, os, pandas as pd, time, geocoder, sys
import requests.packages.urllib3 as urllib3

def download_msa_data(url, dest_path):
    res = requests.get(url)
    if res.status_code == requests.codes.ok:
        with open(dest_path, 'wb') as f:
            f.write(res.content)

def get_mean_coords(county_list):
    coords_list = []
    for county in county_list:
        retry_count = 0
        coords = geocoder.google(county).latlng
        while coords is None:
            print('retrying for ' + county)
            time.sleep(retry_count + 1)
            retry_count += 1
            if retry_count > 10:
                print(county)
                raise Exception
            coords = geocoder.google(county).latlng
        coords_list.append(tuple(coords))
    return tuple(map(lambda y: sum(y) / float(len(y)), zip(*coords_list)))

if __name__ == '__main__':
    #  msa_url = 'https://www.census.gov/population/estimates/metro-city/0312msa.txt'
    #  path_to_file = os.path.join(os.environ['DATA_PATH'],  'external', 'msa.txt')
    #  download_msa_data(msa_url, path_to_file)
