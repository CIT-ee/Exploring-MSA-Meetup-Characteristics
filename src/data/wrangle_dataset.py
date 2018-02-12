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

def batchify_data(path_to_source, path_to_dest, batch_size):
    '''Break a dataframe up into smaller batches to support parallel execution
        
    Keyword arguments:
    path_to_source -- path to the source dataframe (csv) to break up 
                        ( default: None  )
    path_to_dump -- path to where the batched dataframes (csv) need to be dumped
                    ( default: None  )
    batch_size -- size of the batches ( default: nrows of dataframe  )
    '''
    source_df = pd.read_csv(path_to_source, encoding='latin1')
    nrows, _ = source_df.shape

    print('\nPreparing to batchify the dataframe. Please wait ..')
    for _idx, start in enumerate(range(0, nrows, batch_size)):
        stop = start + batch_size
        batch_df = source_df.iloc[start:, :] if stop > nrows else source_df.iloc[start:stop, :]
        batch_df.to_csv(path_to_dump.format(idx=_idx), encoding='latin1', index=False)
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
    for path in src_paths:
        df_batches.append(pd.read_csv(path, encoding=encoding))
    dest_df = pd.concat(df_batches).drop_duplicates().reset_index(drop=True)
    print('Stitchification of dataframe completed! Dumping data to {}\n'.format(path_to_dest))
    dest_df.to_csv(path_to_dest, encoding=encoding, index=False)

def add_msa_data(path_to_source, path_to_dest, src_loc_fields, dest_loc_fields, data_format):
    '''Gathers MSA data (code and name) for the locations present in the dataframe 
    in question and concatenates the colleced data to the same

    Keyword arguments:
    path_to_source -- path to the source data frame (csv) to which the MSA data
                        is to be added ( default: None  )
    path_to_dest -- path to the csv file with the dataframe augmented with the
                    MSA data ( default: None  )
    src_loc_fields -- list of fields in the source dataframe to serve as the 
                        geolocation basis for the process ( default: []  )
    dest_loc_fields -- list of geolocation fields to be added to the dataframe,
                        usually just the MSA name and code ( default: []  )
    data_format -- qualifier to be supplied to the msa-mapping module, whether
                    to start from an address or lat-lon pair ( default: address  )
    '''
    source_df = pd.read_csv(path_to_source, encoding='latin1')
    print('\nPreparing to add MSA data to the data frame in question. Please wait ..')
    src_loc_df = source_df[ src_loc_fields  ]
    msa_mapping_client = MSAMapper(src_loc_df.fillna(''))
    dest_loc_df = msa_mapping_client.map_data(data_format)
    dest_df = pd.concat([ source_df, dest_loc_df[ dest_loc_fields  ]  ], axis=1)

    print('Adding MSA data to dataframe completed! Dumping data to {}'.format(path_to_dest))
    dest_df.to_csv(path_to_dest, encoding='utf-8', index=False)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--op', help='operation to perform')
    parser.add_argument('--endpoint', help='meetup endpoint to work on')
    parser.add_argument('--query', default='', help='subset of endpoint data to work on')
    parser.add_argument('--batch', type=int, help='batch idx to operate on')

    args = parser.parse_args()

    if args.op == 'batchify':
        pass # TODO

    elif args.op == 'stitchify':
        assert args.endpoint is not None, 'Please choose endpoint to operate on first!'

        source_key = raw_input('Please enter source keyword: ')
        dest_key = raw_input('Please enter destination keyword: ')

        path_to_src_dir = os.path.dirname(path_to[source_key])
        path_to_source = path_to_src_dir.format(endpoint=args.endpoint, query=args.query)
        path_to_dest = path_to[dest_key].format(endpoint=args.endpoint, query=args.query)

        _assert_paths(path_to_source, path_to_dest)

        stitch_batch_data(path_to_source, path_to_dest, 'utf-8') 

    elif args.op == 'add_msa':
        assert args.endpoint is not None, 'Please choose endpoint to operate on first!'

        #  set the paths to source and destination
        if args.batch is None:
            path_to_source = path_to['scraped_endpoint'].format(endpoint=args.endpoint, query=args.query)
            path_to_dest = path_to['with_msa_endpoint'].format(endpoint=args.endpoint, query=args.query)
        else:
            path_to_source = path_to['scraped_batch'].format(endpoint=args.endpoint, query=args.query, idx=args.batch)
            path_to_dest = path_to['with_msa_batch'].format(endpoint=args.endpoint, query=args.query, idx=args.batch)

        _assert_paths(path_to_source, path_to_dest)

        add_msa_data(path_to_source, path_to_dest, [ 'lon', 'lat' ], [ 'MSA_NAME', 'MSA_CODE' ], 'lat-lon' )
