from __future__ import print_function
import sys, os, json, pandas as pd, geocoder, pdb, requests.packages.urllib3 as urllib3

sys.path.insert(0, os.environ['PROJECT_PATH']) 
urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)


from config.resources import data_paths
from src.data.helper_utils.msa_data_builder import get_mean_coords
from src.data.helper_utils.meetup_scraper import fetch_events, filter_events 


meetup_api_urls = {
    'events_url': 'https://api.meetup.com/find/events?photo-host=public&sig_id=236706760&radius=smart&lon={lng}&lat={lat}&sig=073c382d765e9deee91240dcf21576438d764088'
}

def build_msa_coords_df(path_to_file):
    msa_coords_df = pd.DataFrame(columns=('Code', 'Name', 'Latitude', 'Longitude'))
    cbsa_df = pd.read_csv(path_to_file, encoding='latin1')

    #filter out the rows which are not Metropolitan Statistical Areas
    msa_codes_df = cbsa_df.loc[cbsa_df.iloc[:, 4] == 'Metropolitan Statistical Area']
    counter, county_list = 0, []
    msa_code, msa_name, msa_coords = None, None, None
    for index, row in msa_codes_df.iterrows():
        #  pdb.set_trace()
        if msa_code != row['CBSA Code'] and len(county_list) > 0:
            msa_coords = get_mean_coords(county_list)
            msa_coords_df.loc[counter] = [int(msa_code), msa_name, msa_coords[0], msa_coords[1]]
            county_list = []
            counter += 1
            print('{} MSAs explored'.format(counter), end='\r',)
        msa_code, msa_name = row['CBSA Code'], row['CBSA Title']
        county_list.append(row['County/County Equivalent'])

    print("\nSample Data:\n", msa_coords_df.head())
    print("\nWriting data to " + data_paths['msa_coords'])
    msa_coords_df.to_csv(data_paths['msa_coords'], index=False, encoding='latin1')

def build_meetups_msa_mapping(path_to_src, path_to_dest):
    msa_coords_df = pd.read_csv(path_to_src, encoding='latin1')
    msa_meetup_dict, events_url = {}, meetup_api_urls['events_url']
    #  print('\nProceeding to fetch meetup event data for {} MSAs.\n'.format(msa_coords_df.shape[0]))
    for index, row in msa_coords_df.iterrows():
        #  pdb.set_trace()
        msa_name, msa_lat, msa_lng = row['Name'], row['Latitude'], row['Longitude']
        events = fetch_events(events_url.format(lat=msa_lat, lng=msa_lng), None)
        filtered_events = filter_events(events, ['group'])
        msa_meetup_dict[msa_name] = filtered_events
        print('Fetched events for {} MSAs'.format(index))
        
    print('\nDumping event data to {}\n'.format(path_to_dest))
    with open(path_to_dest, 'w') as f:
        json.dump(msa_meetup_dict, f)
    #  pass

if __name__ == '__main__':
    path_to_msa_codes, path_to_msa_coords, path_to_msa_meetup_bridge = data_paths['msa_codes'], data_paths['msa_coords'], data_paths['msa_meetups_bridge'] 
    if not os.path.isfile(path_to_msa_coords):
        build_msa_coords_df(path_to_msa_codes)
    build_meetups_msa_mapping(path_to_msa_coords, path_to_msa_meetup_bridge)
