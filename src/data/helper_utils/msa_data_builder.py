from __future__ import print_function

import requests, os, pandas as pd, time, geocoder, sys
import requests.packages.urllib3 as urllib3

def download_msa_data(url, dest_path):
    '''Download csv file with MSA information from specified url
    
    Keyword arguments:
    url -- url to download file from (default None)
    dest_path -- path to where the downloaded file needs to be saved at (default None)
    '''
    res = requests.get(url)
    if res.status_code == requests.codes.ok:
        with open(dest_path, 'wb') as f:
            f.write(res.content)

def get_mean_coords(county_list):
    '''Calculate the centroid of specified coordinates
    
    Since most maps APIs (Google in this case) have rate limits,
    if the request does not return a proper response, there is a
    provision for making upto 10 (magic number) retries with gaps
    between subsequent retries increasing in arithmetic progression
    (lowest waiting time during debugging)
    
    Keyword arguments:
    county_list -- list of county names (default [])
    '''
    coords_list = []

    for county in county_list:
        retry_count = 0
        coords = geocoder.google(county).latlng

        #  retry until a valid response is returned
        while coords is None:
            time.sleep(retry_count + 1)
            retry_count += 1

            #  for debugging purposes
            if retry_count > 10:
                print("Coudn't get geolocation of " + county)
                raise Exception

            coords = geocoder.google(county).latlng # retry

        coords_list.append(tuple(coords))

    #  calculate the mean of n (x,y) tuples
    return tuple(map(lambda y: sum(y) / float(len(y)), zip(*coords_list)))

if __name__ == '__main__':
    '''Test script functionality with code stub'''
    #  msa_url = 'https://www.census.gov/population/estimates/metro-city/0312msa.txt'
    #  path_to_file = os.path.join(os.environ['DATA_PATH'],  'external', 'msa.txt')
    #  download_msa_data(msa_url, path_to_file)
    pass
