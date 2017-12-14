from __future__ import print_function
import sys, os, json, argparse, pandas as pd, geocoder, pdb, requests.packages.urllib3 as urllib3
from itertools import islice

sys.path.insert(0, os.environ['PROJECT_PATH']) # point python interpreter to top of project dir 

#  suppress ServerNameIndication and InsecurePlatform warnings
urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)

#  import local modules
from config.resources import path_to
from config.api_specs import props_for
from src.data.helper_utils.msa_data_builder import get_mean_coords
from src.data.helper_utils.meetup_scraper import ( fetch_paginated_data, 
                                                get_df_from_nested_dicts, get_chkpnt )

meetup_endpoint_for = {
    'events': {
        'topics': 'https://api.meetup.com/find/events?&sign=true&photo-host=public&lon={lon}&fields={optional_fields}&lat={lat}&only={fields}&key={api_key}',
        'attendance': 'https://api.meetup.com/find/events?&sign=true&photo-host=public&lon={lon}&fields={optional_fields}&lat={lat}&only={fields}&key={api_key}'
    },
    'locations': 'https://api.meetup.com/find/locations?&sign=true&photo-host=public&lon={lon}&lat={lat}&only={fields}&key={key}'
}

def _add_location_information(event_ls, lat, lon):
    for event in event_ls:
        event['latitude'], event['longitude'] = lat, lon
    return event_ls

def build_meetup_locations_df(path_to_dest, start_coords, end_coords, coords_step, prop_dict, save_freq=None, use_checkpoint=False):
    '''Build a dataframe consisting of Meetup locations in US cities.
    
    Since, we are using querying the api using freeform text, the signed url
    changes for each request and thus cannot be used for our purposes with ease.
    Additionally, since we are using city names for the freeform text in the
    query, non-US Meetup cities with the same name are returned. For now, they
    are filtered out. Finally, even after using request throttling to stay within
    the API's request rate limits, the server disconnects without warning. To
    overcome that, checkpointing is employed.
    
    Keyword arguments:
    path_to_dest -- path to csv file to be created as a result of this method
    start_coords -- starting coordinates tuple for location scanning
    end_coords -- ending coordinates tuple for location scanning
    coords_step -- stepping factor for the coordinates in the location scanning
    prop_dict -- a dictionary of properties that are to form the dataframe
                column names and used to filter the api request (default: {})
    save_freq -- interval (in terms of cities explored) after which to 
                checkpoint (default: None)
    use_checkpoint -- flag indicating whether to resume from a previous
                    checkpoint or not (default: False)
    '''
    locations_endpoint, counter, num_locs = meetup_endpoint_for['locations'], 0, 0
    start_lon, start_lat = start_coords
    end_lon, end_lat = end_coords
    lon_step, lat_step = coords_step
    field_names = "%2C".join(list(prop_dict.values()))

    #  load target dataframe from a checkpoint if specified
    if use_checkpoint:
        scraping_stats, chkpnt_path = get_chkpnt(path_to['raw']['chkpnts']['locations'])
        start_lon, start_lat, num_locs = scraping_stats
        meetup_locations_df = pd.read_csv(chkpnt_path, encoding='latin1')
    else:
        meetup_locations_df = pd.DataFrame(columns=prop_dict.keys())

    print('\nBuilding meetup locations dataframe. Please wait..')
    for lon in range(start_lon, end_lon, lon_step): 
        for lat in range(start_lat, end_lat, lat_step):

            #  not sure why this needs to be done, but raises an exception
            #  when not put in a try except block
            try:
                locations_url = locations_endpoint.format(lat=lat, lon=lon, \
                                    fields=field_names, key=os.environ['API_KEY'])

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

                    meetup_locations_df.loc[num_locs] = [ location[prop] for prop in list(prop_dict.values()) ]
                    num_locs += 1

            counter += 1

            print('Scanned {} coords (currently on ({}, {})) for locations. Found {}'.format(counter, lon, lat, num_locs), end='\r',)

            #  checkpoint at regular intervals if interval is specified
            if save_freq is not None and ( counter % save_freq ) == 0:
                print('\nMaking checkpoint: Found {num_loc} locations\n'.format(num_loc=num_locs))
                chkpnt_path = path_to['meetup_locations_chkpnt'].format(num_loc=num_locs, lat=lat, lon=lon)
                meetup_locations_df.to_csv(chkpnt_path, index=False, encoding='latin1')

    print('\nBuilding Meetup locations dataframe complete! Dumping event data to {}\n'.format(path_to_dest))
    meetup_locations_df.drop_duplicates(inplace=True)
    meetup_locations_df.to_csv(path_to_dest, index=False, encoding='latin1')

def build_meetup_events_data(path_to_src, path_to_dest, query_type, fields, subfields, save_freq=None, use_checkpoint=False):
    '''Build a mapping between meetup locations and the events happening in it.

    Even after using request throttling to stay within the API's request rate 
    limits, the server disconnects without warning. To overcome that, 
    checkpointing is employed.
    
    Keyword arguments:
    path_to_src -- path to csv file with MSA name and coordinates (default None)
    path_to_dest -- path to json file with the mapping between MSA and events (default None)
    query_type -- type of data to query from the endpoint
    fields -- fields to filter the request with (default: None)
    subfields -- subfields to filter the requests with (default: None)
    save_freq -- interval (in terms of cities explored) after which to 
                checkpoint (default: None)
    use_checkpoint -- flag indicating whether to resume from a previous
    '''
    meetup_locations_df = pd.read_csv(path_to_src, encoding='latin1')
    events_endpoint, num_events, num_locs, start_idx = meetup_endpoint_for['events'][query_type], 0, 0, 0

    #  load target data store from a checkpoint if specified
    if use_checkpoint:
        scraping_stats, chkpnt_path = get_chkpnt(path_to['raw']['chkpnts']['events'], query_type)
        start_idx, num_events, num_locs = scraping_stats
        meetup_events_df = pd.read_csv(chkpnt_path, encoding='latin1')
    else:
        meetup_events_df = pd.DataFrame(columns= fields + [ 'latitude', 'longitude' ]) 

    print('\nBuilding meetup location - meetup event bridge. Please wait..')
    #  start iterating over dataframe from last stopping point
    for index, row in islice(meetup_locations_df.iterrows(), start_idx, None):

        #  pull the meetup location coordinates, query for events around those 
        #  coordinates, and store interesting properties from the response
        loc_lat, loc_lng = row['Latitude'], row['Longitude']
        field_names, subfield_name = ",".join(fields), ",".join(subfields)
        events_url = events_endpoint.format(lat=loc_lat, lon=loc_lng, \
                        fields=field_names, optional_fields=subfield_name, \
                        api_key=os.environ['API_KEY'])
        events_data = fetch_paginated_data(events_url, None)
        num_locs += 1

        #  skip adding to the dataframe if request returned no data in response
        if len(events_data) == 0:
            continue
        
        events_data = _add_location_information(events_data, loc_lat, loc_lng)
        events_batch_df = get_df_from_nested_dicts(events_data, \
                                meetup_events_df.columns.tolist())
        num_events += len(events_data)
        meetup_events_df = meetup_events_df.append(events_batch_df)

        #  checkpoint at regular intervals if interval is specified
        if save_freq is not None and ( num_locs % save_freq ) == 0: 

            #  trim dataframe of redundant rows for smaller write size
            meetup_events_df.drop_duplicates(subset='id', inplace=True)
            num_events = meetup_events_df.shape[0]

            print('\nMaking checkpoint: Found {num_events} in {num_loc}\n'.format(num_loc=num_locs, num_events=num_events))
            chkpnt_fname_template = "meetup_events_{query}_{loc_idx}_{num_events}_{num_locs}.csv"
            chkpnt_fname = chkpnt_fname_template.format(query=query_type, num_locs=num_locs, \
                                                        num_events=num_events, loc_idx=index)
            chkpnt_path = os.path.join(path_to['raw']['chkpnts']['events'], \
                                        chkpnt_fname)
            meetup_events_df.to_csv(chkpnt_path, index=False, encoding='latin1')

        print('Fetched events for {} locations'.format(num_locs), end='\r',)
        
    print('\nBuilding meetup location - meetup event bridge complete! Dumping event data to {}\n'.format(path_to_dest))

    meetup_events_df.drop_duplicates(inplace=True)
    meetup_events_df.to_csv(path_to_dest, index=False, encoding='latin1')

if __name__ == '__main__':
    '''Test script functionality with code stub'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpoint', default='locations', help='the meetup api endpoint to scrape')
    parser.add_argument('--query', default=None, help='optional subfields we are interested in')
    parser.add_argument('--resume', action='store_true', help='flag: resume from checkpoint or not')
    parser.add_argument('--chkpnt_freq', default=None, type=int, help='frequency at which to perform checkpoints' )
    parser.add_argument('--batch', type=int, default=0, help='batch number of the locations to operate on')

    args = parser.parse_args()

    path_to_chkpnts = path_to['raw']['chkpnts'][args.endpoint]
        
    #  check if there is a checkpoint store to resume from 
    if args.resume:
        assert len(os.listdir(path_to_chkpnts)) > 0, \
            'Sorry no checkpoints found at {}. Please create checkpoints first'.format(path_to_chkpnts)
    
    #  check there is directory to store checkpoints in
    if args.chkpnt_freq is not None:
        assert os.path.exists(path_to_chkpnts), \
            'Sorry the checkpoint directory at {} does not exist yet!'.format(path_to_chkpnts)

    #  check which api endpoint to scrape
    if args.endpoint == 'locations':
        
        build_meetup_locations_df(path_to['meetup_locations'], (-125, 24), (-67, 49), (1,1),
                                props_for[args.endpoint], args.chkpnt_freq, args.resume)

    elif args.endpoint == 'events':

        #  dependency: check if the locations dataset exists
        path_to_locs = path_to['meetup_locations'].format(args.batch)
        assert os.path.exists(path_to_locs), \
            'Events scraping has a dependency on locations data. Please build that first!'

        path_to_dest = path_to['meetup_events'][args.query].format(args.batch)

        path_to_dest_dir = os.path.dirname(path_to_dest)
        assert os.path.exists(path_to_dest_dir), \
            'Destination directory does not exist at {}. Please build that first!'.format(path_to_dest_dir)

        props_for_query = props_for[args.endpoint][args.query]

        build_meetup_events_data(path_to_locs, path_to_dest, args.query, 
                                props_for_query['only'], props_for_query['fields'], \
                                args.chkpnt_freq, args.resume)
