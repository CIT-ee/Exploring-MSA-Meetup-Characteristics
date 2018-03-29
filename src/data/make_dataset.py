from __future__ import print_function
import sys, os, argparse, pandas as pd, requests.packages.urllib3 as urllib3, pdb
from itertools import product, islice

sys.path.insert(0, os.environ['PROJECT_PATH']) # point python interpreter to top of project dir 

#  suppress ServerNameIndication and InsecurePlatform warnings
urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)

#  import local modules
from config.resources import path_to
from config.api_specs import props_for
from src.data.utils import merge_dicts, assert_paths, save_dataframe
from src.data.helper_scripts.meetup_scraper import ( fetch_paginated_data, 
                                                get_df_from_nested_dicts, get_chkpnt )

meetup_endpoint_for = {
    'events': {
        'topics': 'https://api.meetup.com/find/events?&sign=true&photo-host=public&lon={lon}&radius=0&fields={optional_fields}&lat={lat}&only={fields}&key={api_key}',
        'attendance': 'https://api.meetup.com/find/events?&sign=true&photo-host=public&lon={lon}&radius=0&fields={optional_fields}&lat={lat}&only={fields}&key={api_key}'
    },
    'groups': 'https://api.meetup.com/find/groups?&sign=true&photo-host=public&lon={lon}&radius=69&fields={optionals}&lat={lat}&order=distance&page=20&only={fields}&key={api_key}',
    'locations': 'https://api.meetup.com/find/locations?&sign=true&photo-host=public&lon={lon}&lat={lat}&only={fields}&key={key}'
}

def build_meetup_locations_df(paths, lon_range, lat_range, prop_dict, save_freq=None, use_checkpoint=False):
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
    lon_range -- list of longitudes to iterate over (default: [])
    lat_range -- list of latitudes to iterate over (default: [])
    prop_dict -- a dictionary of properties that are to form the dataframe
                column names and used to filter the api request (default: {})
    save_freq -- interval (in terms of cities explored) after which to 
                checkpoint (default: None)
    use_checkpoint -- flag indicating whether to resume from a previous
                    checkpoint or not (default: False)
    '''
    path_to_chkpnt_dir, path_to_dest = paths.values()
    df_batches, locations_endpoint = [], meetup_endpoint_for['locations']
    counter, num_locs, lon_start_idx, lat_start_idx = 0, 0, 0, 0
    field_names = "%2C".join(list(prop_dict.values()))

    #  load target dataframe from a checkpoint if specified
    if use_checkpoint:
        scraping_stats, chkpnt_path = get_chkpnt(path_to_chkpnt_dir, None)
        start_lon, start_lat, num_locs = scraping_stats
        lon_start_idx, lat_start_idx = lon_range.index(start_lon), lat_range.index(start_lat) 
        df_batches.append(pd.read_csv(chkpnt_path, encoding='latin1'))

    print('\nBuilding meetup locations dataframe. Please wait..')
    for lon in islice(lon_range, lon_start_idx, None):
        for lat in islice(lat_range, lat_start_idx, None):
            #  not sure why this needs to be done, but raises an exception
            #  when not put in a try except block
            try:
                locations_url = locations_endpoint.format(lat=lat, lon=lon, \
                                fields=field_names, key=os.environ['API_KEY'])
            except UnicodeEncodeError:
                pass

            #  make the request to the api endpoint
            locations = fetch_paginated_data(locations_url, None) 

            counter += 1
            print('Scanned {} coords (currently on ({}, {})) for locations'.format(counter, lon, lat), end='\r',)

            #  skip adding to the dataframe if request returned no data in response
            if len(locations) == 0: continue

            filtered_locs = list(filter(lambda x: x['localized_country_name'] == 'USA', locations))
            df_batches.append(pd.DataFrame(filtered_locs))
            num_locs += df_batches[-1].shape[0]

            #  checkpoint at regular intervals if interval is specified
            if save_freq is not None and ( counter % save_freq ) == 0:
                print('\nMaking checkpoint: Found {num_loc} locations\n'.format(num_loc=num_locs))
                chkpnt_fname = "meetup_locations_{}_{}_{}.csv".format(lon, lat, num_locs)
                chkpnt_path = os.path.join(path_to_chkpnt_dir, chkpnt_fname)
                save_dataframe(chkpnt_path, df_batches, None)

    print('\nBuilding Meetup locations dataframe complete! Dumping event data to {}\n'.format(path_to_dest))
    save_dataframe(path_to_dest, df_batches, None)

def build_meetup_events_data(paths, query_type, fields, subfields, save_freq=None, use_checkpoint=False):
    '''Build a mapping between meetup locations and the events happening in it.

    Even after using request throttling to stay within the API's request rate 
    limits, the server disconnects without warning. To overcome that, 
    checkpointing is employed.
    
    Keyword arguments:
    path_to_src -- path to csv file with MSA name and coordinates (default None)
    path_to_dest -- path to csv file with the mapping between MSA and events (default None)
    query_type -- type of data to query from the endpoint
    fields -- fields to filter the request with (default: None)
    subfields -- subfields to filter the requests with (default: None)
    save_freq -- interval (in terms of cities explored) after which to 
                checkpoint (default: None)
    use_checkpoint -- flag indicating whether to resume from a previous
    '''
    path_to_chkpnt_dir, path_to_source, path_to_dest = paths.values()
    meetup_locations_df = pd.read_csv(path_to_source, encoding='latin1')
    events_endpoint, df_batches = meetup_endpoint_for['events'][query_type], []
    num_events, num_locs, start_idx = 0, 0, 0
    chkpnt_fname_template = "meetup_events_{loc_idx}_{num_events}_{num_locs}.csv"

    #  load target data store from a checkpoint if specified
    if use_checkpoint:
        scraping_stats, chkpnt_path = get_chkpnt(path_to_chkpnt_dir, query_type)
        start_idx, num_events, num_locs = scraping_stats
        df_batches.append(pd.read_csv(chkpnt_path, encoding='latin1'))

    print('\nBuilding meetup location - meetup event bridge. Please wait..')
    #  start iterating over dataframe from last stopping point
    for index, row in islice(meetup_locations_df.iterrows(), start_idx, None):
        #  pull the meetup location coordinates, query for events around those 
        #  coordinates, and store interesting properties from the response
        loc_lat, loc_lon = row['Latitude'], row['Longitude']
        field_names, subfield_name = ",".join(fields), ",".join(subfields)
        events_url = events_endpoint.format(lat=loc_lat, lon=loc_lon, \
                        fields=field_names, optional_fields=subfield_name, \
                        api_key=os.environ['API_KEY'])
        events_data = fetch_paginated_data(events_url, None)
        num_locs += 1
        print('Fetched events for {} locations'.format(num_locs), end='\r',)

        #  skip adding to the dataframe if request returned no data in response
        if len(events_data) == 0: continue
        
        #  add location data explicitly
        events_data = list(map(lambda d: merge_dicts(d, { 'lat': loc_lat, 'lon': loc_lon }), events_data))

        #  flatten the dicts and convert the batch of event data to dataframe
        df_batches.append(get_df_from_nested_dicts(events_data))
        num_events += df_batches[-1].shape[0]

        #  checkpoint at regular intervals if interval is specified
        if save_freq is not None and ( num_locs % save_freq ) == 0: 
            print('\nMaking checkpoint: Processed {} locations\n'.format(num_locs))
            chkpnt_fname = chkpnt_fname_template.format(index, num_events, num_locs)
            chkpnt_path = os.path.join(path_to_chkpnt_dir, chkpnt_fname)
            save_dataframe(chkpnt_path, df_batches, None)
        
    print('\nBuilding meetup location - meetup event bridge complete! Dumping event data to {}\n'.format(path_to_dest))
    save_dataframe(path_to_dest, df_batches, None)

def build_meetup_groups_data(paths, coord_ls, prop_dict, save_freq=None, use_checkpoint=False):
    '''Build a mapping between meetup locations and the groups formed around it.

    Even after using request throttling to stay within the API's request rate 
    limits, the server disconnects without warning. To overcome that, 
    checkpointing is employed.
    
    Keyword arguments:
    path_to_src -- path to csv file with MSA name and coordinates (default: None)
    path_to_dest -- path to csv file with the mapping between MSA and groups (default: None)
    fields -- fields to filter the request with (default: None)
    optionals -- optional fields to include in response (default: None)
    save_freq -- interval (in terms of cities explored) after which to 
                checkpoint (default: None)
    use_checkpoint -- flag indicating whether to resume from a previous
    '''
    fields, optionals = prop_dict['only'], prop_dict['fields']
    path_to_chkpnt_dir, path_to_dest = paths.values()
    groups_endpoint = meetup_endpoint_for['groups']
    df_batches, num_groups, coord_start_idx = [], 0, 0
    chkpnt_fname_template = "meetup_groups_{}_{}.csv"

    #  load target data store from a checkpoint if specified
    if use_checkpoint:
        scraping_stats, chkpnt_path = get_chkpnt(path_to_chkpnt_dir, None)
        coord_start_idx, num_groups = scraping_stats
        df_batches.append(pd.read_csv(chkpnt_path, encoding='latin1'))

    print('\nBuilding meetup location - meetup groups bridge. Please wait..')
    #  start iterating over geoloc coordinates from last stopping point
    for _idx, coord in enumerate(islice(coord_ls, coord_start_idx, None)):
        #  query for groups around current coordinates 
        lon, lat = coord
        print('Processing location - lon: {}, lat: {}'.format(lon, lat))
        field_names, optionals_names = ",".join(fields), ",".join(optionals)
        groups_url = groups_endpoint.format(lat=lat, lon=lon, \
                        fields=field_names, optionals=optionals_names, \
                        api_key=os.environ['API_KEY'])
        groups_data = fetch_paginated_data(groups_url, None)
        num_locs = coord_start_idx + _idx + 1
    
        #  skip adding to the dataframe if request returned no data in response
        if len(groups_data) == 0: continue
        
        df_batches.append(get_df_from_nested_dicts(groups_data)) 
        num_groups += df_batches[-1].shape[0]

        #  checkpoint at regular intervals if interval is specified
        if save_freq is not None and ( num_locs % save_freq ) == 0: 
            print('\nMaking checkpoint: Processed {} locations\n'.format(num_locs))
            chkpnt_fname = chkpnt_fname_template.format(num_locs, num_groups)
            chkpnt_path = os.path.join(path_to_chkpnt_dir, chkpnt_fname)
            save_dataframe(chkpnt_path, df_batches, None, 'utf-8')

        print('Fetched groups from {} locations'.format(num_locs))
    
    print('\nBuilding meetup location - meetup groups bridge complete! Dumping groups data to {}\n'.format(path_to_dest))
    save_dataframe(path_to_dest, df_batches, None, 'utf-8')

if __name__ == '__main__':
    '''Test script functionality with code stub'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpoint', default='locations', help='the meetup api endpoint to scrape')
    parser.add_argument('--query', default='', help='optional subfields we are interested in')
    parser.add_argument('--resume', action='store_true', help='flag: resume from checkpoint or not')
    parser.add_argument('--chkpnt_freq', default=None, type=int, help='frequency at which to perform checkpoints' )
    parser.add_argument('--batch', type=int, default=0, help='batch number of the locations to operate on')

    args = parser.parse_args()

    paths = { 'chkpnt': path_to['chkpnts'].format(endpoint=args.endpoint) }

    #  check if there is a checkpoint store to resume from 
    if args.resume:
        assert len(os.listdir(path_to_chkpnt_dir)) > 0, \
            'Sorry no checkpoints found at {}. Please create checkpoints first'.format(path_to_chkpnt_dir)

    #  check if there is a checkpoint directory, create it if not
    if args.chkpnt_freq is not None and os.path.exists(path_to_chkpnt_dir):
        os.makedirs(path_to_chkpnt_dir)
    
    #  check which api endpoint to scrape
    if args.endpoint == 'locations':
        paths['dest'] = path_to['meetup_locations']
        build_meetup_locations_df(paths, range(-125, -67, 1), range(24, 49, 1), 
                                props_for[args.endpoint], args.chkpnt_freq, args.resume)

    elif args.endpoint == 'events':
        if args.batch is None:
            path_to_source = path_to['meetup_locations']
            path_to_dest = path_to['scraped_endpoint'].format(endpoint=args.endpoint, query=args.query)
        else:
            path_to_source = path_to['meetup_locations_batch'].format(args.batch)
            path_to_dest = path_to['scraped_batch'].format(endpoint=args.endpoint,
                                                    query=args.query, idx=args.batch)

        assert_paths(path_to_source, path_to_dest)

        paths['src'], paths['dest'] = path_to_source, path_to_dest
        props_for_query = props_for[args.endpoint][args.query]

        build_meetup_events_data(paths, args.query, props_for_query['only'], 
                                props_for_query['fields'], args.chkpnt_freq, args.resume)
    
    elif args.endpoint == 'groups':
        geo_coords = list(product(range(-125, -67, 1), range(26, 49, 1)))

        if args.batch is None:
            path_to_dest = path_to['scraped_endpoint'].format(endpoint=args.endpoint, query=args.query)
        else:
            start_idx, stop_idx = args.batch * 5, (args.batch + 1) * 5
            coord_ls = geo_coords[start_idx:] if stop_idx >= len(geo_coords) \
                        else geo_coords[start_idx:stop_idx]
            path_to_dest = path_to['scraped_batch'].format(endpoint=args.endpoint, query=args.query, idx=args.batch)

        assert_paths(None, path_to_dest)

        paths['dest'] = path_to_dest
        build_meetup_groups_data(paths, coord_ls, props_for[args.endpoint], 
                                args.chkpnt_freq, args.resume)
