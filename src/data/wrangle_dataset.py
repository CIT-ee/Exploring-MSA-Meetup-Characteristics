from __future__ import print_function

import os, sys
sys.path.insert(0, os.environ['PROJECT_PATH']) # point python interpreter to top of project dir

import argparse, pandas as pd, geocoder, pdb, requests.packages.urllib3 as urllib3
#  suppress ServerNameIndication and InsecurePlatform warnings
urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)

from config.resources import path_to
from config.api_specs import props_for 
from src.data.msa_mapper.map_loc_to_msa import MSAMapper

def _assert_paths(path_to_source, path_to_dest):
    '''Assert the paths provided are valid
            
    Keyword arguments:
    path_to_source -- path to the source ( default: None  )
    path_to_dest -- path to the destination ( default: None  )
    '''
    assert os.path.exists(path_to_source), \
        'Please create file at {} first!'.format(path_to_source)

    assert os.path.exists(os.path.dirname(path_to_dest)), \
        'Please create directory at {} first!'.format(os.path.dirname(path_to_dest))

def batchify_data(path_to_source, path_to_dest, nb_batches, encoding='latin1'):
    '''Break a dataframe up into smaller batches to support parallel execution
        
    Keyword arguments:
    path_to_source -- path to the source dataframe (csv) to break up 
                        ( default: None  )
    path_to_dump -- path to where the batched dataframes (csv) need to be dumped
                    ( default: None  )
    batch_size -- number of batches to create ( default: 1 )
    '''
    source_df = pd.read_csv(path_to_source, encoding='latin1')
    nrows, _ = source_df.shape
    batch_size = int(nrows / nb_batches)
    
    print('\nPreparing to split the dataframe into {} batches of {} rows. Please wait ..'.format(nb_batches, batch_size))
    for _idx, start in enumerate(range(0, nrows, batch_size)):
        stop = start + batch_size
        batch_df = source_df.iloc[start:, :] if stop > nrows else source_df.iloc[start:stop, :]
        batch_df.to_csv(path_to_dest.format(idx=_idx), encoding=encoding, index=False)
    print('Batchification of dataframe completed!\n')

def stitch_batch_data(path_to_source, path_to_dest, encoding='latin1'):
    '''Consolidate batches of data into a master dataset
    
    Keyword arguments:
    path_to_source -- path to directory containing the data batches ( default: None )
    path_to_dest -- path to the consolidated csv file ( default: None )
    encoding -- encoding to use for loading and dumping the dataframes ( default: 'latin1' )
    '''
    src_paths = [ os.path.join(path_to_source, fname) for fname in os.listdir(path_to_source) ]
    df_batches = []
    print('\nPreparing to stitchify the dataframe. Please wait ..')
    for _idx, path in enumerate(src_paths):
        print('Processed {} batches..'.format(_idx))
        df_batches.append(pd.read_csv(path, encoding=encoding))
    dest_df = pd.concat(df_batches).drop_duplicates().reset_index(drop=True)
    print('Stitchification of dataframe completed! Dumping data to {}\n'.format(path_to_dest))
    dest_df.to_csv(path_to_dest, encoding=encoding, index=False)

def add_census_data(path_to_source, path_to_dest, src_loc_fields, census_name, data_format):
    '''Gathers MSA data (code and name) for the locations present in the dataframe 
    in question and concatenates the colleced data to the same

    Keyword arguments:
    path_to_source -- path to the source data frame (csv) to which the MSA data
                        is to be added ( default: None  )
    path_to_dest -- path to the csv file with the dataframe augmented with the
                    MSA data ( default: None  )
    src_loc_fields -- list of fields in the source dataframe to serve as the 
                        geolocation basis for the process ( default: []  )
    census_name -- name of the census level interested in ( default: None )
    data_format -- qualifier to be supplied to the msa-mapping module, whether
                    to start from an address or lat-lon pair ( default: address  )
    '''
    source_fname = os.path.basename(path_to_source)
    source_df = pd.read_csv(path_to_source, encoding='latin1')
    print('\nPreparing to add MSA data to {}. Please wait ..'.format(source_fname))
    src_loc_df = source_df[ src_loc_fields  ]
    msa_mapping_client = MSAMapper(src_loc_df.fillna(''))

    dest_loc_fields = [ census_name.upper() + '_NAME', census_name.upper() + '_CODE' ]
    dest_loc_df = msa_mapping_client.map_data(census_name, dest_loc_fields, data_format)
    dest_df = pd.concat([ source_df, dest_loc_df[ dest_loc_fields  ]  ], axis=1)

    print('Adding MSA data to dataframe completed! Dumping data to {}'.format(path_to_dest))
    dest_df.to_csv(path_to_dest, encoding='utf-8', index=False)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--op', help='operation to perform')
    parser.add_argument('--endpoint', help='meetup endpoint to work on')
    parser.add_argument('--query', default='', help='subset of endpoint data to work on')
    parser.add_argument('--census_name', default='msa', help='name of census level to work on')
    parser.add_argument('--batch', type=int, help='batch idx to operate on')
    parser.add_argument('--nb_batches', type=int, default=1, help='number to batches to create')

    args = parser.parse_args()

    if args.op == 'batchify':
        assert args.endpoint is not None, 'Please choose endpoint to operate on first!'

        source_key = raw_input('Please enter source keyword: ')
        dest_key = raw_input('Please enter destination keyword: ')

        path_to_source = path_to[source_key].format(endpoint=args.endpoint, query=args.query)
        path_to_dest = path_to[dest_key].format(endpoint=args.endpoint, query=args.query, idx='{idx}')

        _assert_paths(path_to_source, path_to_dest)

        batchify_data(path_to_source, path_to_dest, args.nb_batches - 1, 'utf-8') 

    elif args.op == 'stitchify':
        assert args.endpoint is not None, 'Please choose endpoint to operate on first!'

        source_key = raw_input('Please enter source keyword: ')
        dest_key = raw_input('Please enter destination keyword: ')

        path_to_src_dir = os.path.dirname(path_to[source_key])
        path_to_source = path_to_src_dir.format(endpoint=args.endpoint, query=args.query)
        path_to_dest = path_to[dest_key].format(endpoint=args.endpoint, query=args.query)

        _assert_paths(path_to_source, path_to_dest)

        stitch_batch_data(path_to_source, path_to_dest, 'utf-8') 

    elif args.op == 'add_census_data':
        assert args.endpoint is not None, 'Please choose endpoint to operate on first!'

        #  set the paths to source and destination
        if args.batch is None:
            path_to_source = path_to['scraped_endpoint'].format(endpoint=args.endpoint, query=args.query)
            path_to_dest = path_to['with_census_endpoint'].format(endpoint=args.endpoint, query=args.query, census=args.census_name)
        else:
            path_to_source = path_to['scraped_batch'].format(endpoint=args.endpoint, query=args.query, idx=args.batch)
            path_to_dest = path_to['with_census_batch'].format(endpoint=args.endpoint, query=args.query, idx=args.batch, census=args.census_name)

        _assert_paths(path_to_source, path_to_dest)

        add_census_data(path_to_source, path_to_dest, [ 'lon', 'lat' ], args.census_name, 'lat-lon' )
