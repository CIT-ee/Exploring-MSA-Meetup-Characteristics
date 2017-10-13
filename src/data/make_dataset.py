from __future__ import print_function
import sys, os, json, argparse, pandas as pd, geocoder, pdb, requests.packages.urllib3 as urllib3
from itertools import islice

sys.path.insert(0, os.environ['PROJECT_PATH']) # point python interpreter to top of project dir 

#  suppress ServerNameIndication and InsecurePlatform warnings
urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)

#  import local modules
from config.resources import path_to
from src.data.helper_utils.msa_data_builder import get_mean_coords
from src.data.helper_utils.meetup_scraper import fetch_paginated_data, filter_events, get_chkpnt 


meetup_endpoint_for = {
    'events': 'https://api.meetup.com/find/events?photo-host=public&sig_id=236706760&radius=smart&lon={lng}&lat={lat}&sig=073c382d765e9deee91240dcf21576438d764088',
    'locations': 'https://api.meetup.com/find/locations?&sign=true&photo-host=public&query={text}&only={fields}&key={api_key}'
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

    print("\nBuilding MSA coordinates dataframe complete! Writing data to " + path_to['msa_coords'] + "\n")
    msa_coords_df.to_csv(path_to['msa_coords'], index=False, encoding='latin1')

def build_meetup_locations_df(path_to_src, path_to_dest, prop_dict, save_freq=None, use_checkpoint=False):
    '''Build a dataframe consisting of Meetup locations in US cities.
    
    Since, we are using querying the api using freeform text, the signed url
    changes for each request and thus cannot be used for our purposes with ease.
    Additionally, since we are using city names for the freeform text in the
    query, non-US Meetup cities with the same name are returned. For now, they
    are filtered out. Finally, even after using request throttling to stay within
    the API's request rate limits, the server disconnects without warning. To
    overcome that, checkpointing is employed.
    
    Keyword arguments:
    path_to_src -- path to csv file with city names (default: None)
    path_to_dest -- path to csv file to be created as a result of this method
    prop_dict -- a dictionaries of properties that are to form the dataframe
                column names and used to filter the api request (default: {})
    save_freq -- interval (in terms of cities explored) after which to 
                checkpoint (default: None)
    use_checkpoint -- flag indicating whether to resume from a previous
                    checkpoint or not (default: False)
    '''
    cities_df = pd.read_csv(path_to_src, encoding='latin1')
    locations_endpoint, counter, start_idx = meetup_endpoint_for['locations'], 0, 0
    
    #  load target dataframe from a checkpoint if specified
    if use_checkpoint:
        start_idx, counter, chkpnt_fname = get_chkpnt(path_to['raw']['chkpnts']['locations'])
        meetup_locations_df = pd.read_csv(chkpnt_fname, encoding='latin1')
    else:
        meetup_locations_df = pd.DataFrame(columns=prop_dict.keys())

    #  start iterating over dataframe from last stopping point
    for index, row in islice(cities_df.iterrows(), start_idx, None):
        city_name = row['NAME']
        field_names = "%2C".join(list(prop_dict.values()))

        try:
            locations_url = locations_endpoint.format(text=city_name, fields=field_names, api_key=os.environ['API_KEY'])

        except UnicodeEncodeError:
            pass

        #  make the request to the api endpoint
        locations = fetch_paginated_data(locations_url, None) 
        
        #  add locations only if response returned any for that city
        if len(locations) > 0:

            for location in locations:

                #  skip locations if not in USA
                if location['localized_country_name'] != 'USA':
                    continue

                meetup_locations_df.loc[counter] = [ value for _, value in list(location.items()) ]
                counter += 1

            print('Fetched locations for {} meetup cities'.format(index), end='\r',)

        #  checkpoint at regular intervals if interval is specified
        if save_freq is not None and ( index % save_freq ) == ( save_freq - 1 ):
            print('\nMaking checkpoint: Found {num_loc} in {num_cities}\n'.format(num_loc=counter, num_cities=index))
            chkpnt_path = path_to['meetup_locations_chkpnt'].format(num_loc=counter, num_cities=index)
            meetup_locations_df.to_csv(chkpnt_path, index=False, encoding='latin1')


    print('\nBuilding Meetup locations dataframe complete! Dumping event data to {}\n'.format(path_to_dest))
    meetup_locations_df.to_csv(path_to['meetup_locations'], index=False, encoding='latin1')

def build_meetups_msa_mapping(path_to_src, path_to_dest):
    '''Build a mapping between MSA and the events happening in it.
    
    Keyword arguments:
    path_to_src -- path to csv file with MSA name and coordinates (default None)
    path_to_dest -- path to json file with the mapping between MSA and events (default None)
    '''
    msa_coords_df = pd.read_csv(path_to_src, encoding='latin1')
    msa_meetup_dict, events_endpoint = {}, meetup_endpoint_for[events]

    for index, row in msa_coords_df.iterrows():

        #  pull the MSA name and coordinates, query for events around those 
        #  coordinates, and store interesting properties from the response, mapped
        #  the MSA in question
        msa_name, msa_lat, msa_lng = row['Name'], row['Latitude'], row['Longitude']
        events_url = events_endpoint.format(lat=msa_lat, lng=msa_lng)
        events = fetch_paginated_data(events_url, None)
        filtered_events = filter_events(events, ['name', 'group'])
        msa_meetup_dict[msa_name] = filtered_events
        print('Fetched events for {} MSAs'.format(index), end='\r',)
        
    print('\nBuilding MSA to Meetup bridge complete! Dumping event data to {}\n'.format(path_to_dest))

    with open(path_to_dest, 'w') as f:
        json.dump(msa_meetup_dict, f)

if __name__ == '__main__':
    '''Test script functionality with code stub'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpoint', default='locations', help='the meetup api endpoint to scrape')
    parser.add_argument('--resume', action='store_true', help='flag: resume from checkpoint or not')
    parser.add_argument('--chkpnt_freq', default=None, type=int, help='frequency at which to perform checkpoints' )

    args = parser.parse_args()

    if args.endpoint == 'locations':
        print('\nBuilding bridge to map MSA to meetup events')
        prop_dict = { 
                'City': 'city',
                'Country': 'localized_country_name', 
                'State': 'state', 
                'ZipCode': 'zip', 
                'Latitude': 'lat',
                'Longitude': 'lon'
        }
        build_meetup_locations_df(path_to['cities'], path_to['meetup_locations'], prop_dict, args.chkpnt_freq, args.resume)

    elif args.endpoint == 'events':
        #  check if csv with MSA coordinates exists, build it if it does not
        if not os.path.isfile(path_to_msa_coords):
            print('\nBuilding dataframe for MSA coordinates..\n')
            build_msa_coords_df(path_to['msa_codes'])

        print('\nBuilding bridge to map MSA to meetup events')
        build_meetups_msa_mapping(path_to['msa_coords'], path_to['msa_meetups_bridge'])
