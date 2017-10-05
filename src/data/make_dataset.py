from __future__ import print_function
import sys, os, json, pandas as pd, geocoder, pdb, requests.packages.urllib3 as urllib3

sys.path.insert(0, os.environ['PROJECT_PATH']) # point python interpreter to top of project dir 

#  suppress ServerNameIndication and InsecurePlatform warnings
urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)

#  import local modules
from config.resources import data_paths
from src.data.helper_utils.msa_data_builder import get_mean_coords
from src.data.helper_utils.meetup_scraper import fetch_events, filter_events 


meetup_api_urls = {
    'events_url': 'https://api.meetup.com/find/events?photo-host=public&sig_id=236706760&radius=smart&lon={lng}&lat={lat}&sig=073c382d765e9deee91240dcf21576438d764088'
}

def build_msa_coords_df(path_to_file):
    '''Build a new dataframe with latitude longitude information for each MSA.
    
    Not all MSA names return a legitimate latlng property when queried through
    Google/Bing Maps API. So, coordinates are indirectly calculated by fetching
    the latitude-longitude tuple for an MSA's constituent counties and then
    calculating the centroid based on those coordinates.

    Keyword arguments:
    path_to_file -- path to csv file with MSA and child county names (default None)
    '''
    cbsa_df = pd.read_csv(path_to_file, encoding='latin1') # base dataframe

    # the dataframe to build
    msa_coords_df = pd.DataFrame(columns=('Code', 'Name', 'Latitude', 'Longitude'))

    #filter out the rows which are not Metropolitan Statistical Areas
    msa_codes_df = cbsa_df.loc[cbsa_df.iloc[:, 4] == 'Metropolitan Statistical Area']
    counter, county_list = 0, []
    msa_code, msa_name, msa_coords = None, None, None

    for index, row in msa_codes_df.iterrows():

        #  check if new row is pertaining to new MSA, in which case calculate
        #  the representative coordinates of the MSA based on the coordinates
        #  of the counties collected so far
        if msa_code != row['CBSA Code'] and len(county_list) > 0:
            msa_coords = get_mean_coords(county_list)
            msa_coords_df.loc[counter] = [int(msa_code), msa_name, msa_coords[0], msa_coords[1]]
            county_list = [] # clear the county list
            counter += 1
            print('{} MSAs explored'.format(counter), end='\r',)
        
        #  store the MSA code, name and child counties while its the same MSA as
        #  the previous row
        msa_code, msa_name = row['CBSA Code'], row['CBSA Title']
        county_list.append(row['County/County Equivalent'])

    print("\nBuilding MSA coordinates dataframe complete! Writing data to " + data_paths['msa_coords'] + "\n")
    msa_coords_df.to_csv(data_paths['msa_coords'], index=False, encoding='latin1')

def build_meetups_msa_mapping(path_to_src, path_to_dest):
    '''Build a mapping between MSA and the events happening in it.
    
    Keyword arguments:
    path_to_src -- path to csv file with MSA name and coordinates (default None)
    path_to_dest -- path to json file with the mapping between MSA and events (default None)
    '''
    msa_coords_df = pd.read_csv(path_to_src, encoding='latin1')
    msa_meetup_dict, events_url = {}, meetup_api_urls['events_url']

    for index, row in msa_coords_df.iterrows():

        #  pull the MSA name and coordinates, query for events around those 
        #  coordinates, and store interesting properties from the response, mapped
        #  the MSA in question
        msa_name, msa_lat, msa_lng = row['Name'], row['Latitude'], row['Longitude']
        events = fetch_events(events_url.format(lat=msa_lat, lng=msa_lng), None)
        filtered_events = filter_events(events, ['name', 'group'])
        msa_meetup_dict[msa_name] = filtered_events
        print('Fetched events for {} MSAs'.format(index), end='\r',)
        
    print('\nBuilding MSA to Meetup bridge complete! Dumping event data to {}\n'.format(path_to_dest))

    with open(path_to_dest, 'w') as f:
        json.dump(msa_meetup_dict, f)

if __name__ == '__main__':
    '''Test script functionality with code stub'''
    path_to_msa_codes, path_to_msa_coords, path_to_msa_meetup_bridge = data_paths['msa_codes'], data_paths['msa_coords'], data_paths['msa_meetups_bridge'] 

    #  check if csv with MSA coordinates exists, build it if it does not
    if not os.path.isfile(path_to_msa_coords):
        print('\nBuilding dataframe for MSA coordinates..\n')
        build_msa_coords_df(path_to_msa_codes)

    print('\nBuilding bridge to map MSA to meetup events')
    build_meetups_msa_mapping(path_to_msa_coords, path_to_msa_meetup_bridge)
