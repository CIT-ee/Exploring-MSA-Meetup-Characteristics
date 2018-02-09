import os, pandas as pd

def assert_paths(path_to_source, path_to_dest):
    '''Assert the paths provided are valid
            
    Keyword arguments:
    path_to_source -- path to the source ( default: None  )
    path_to_dest -- path to the destination ( default: None  )
    '''
    assert path_to_source is None or os.path.exists(path_to_source), \
        'Please create file at {} first!'.format(path_to_source)

    assert path_to_dest is None or os.path.exists(os.path.dirname(path_to_dest)), \
        'Please create directory at {} first!'.format(os.path.dirname(path_to_dest))

def save_dataframe(path_to_dest, df_batches, index, encoding='latin1'):
    '''Concatenate provided list of dataframe batches and save to disk at provided path

    Keyword arguments:
    path_to_dest -- path to save final dataframe at in disk ( default: None  )
    df_batches -- list of dataframe batches to concatenate to form final 
                dataframe ( default: []  )
    index -- column to hash duplicates by ( default: None )
    encoding -- encoding to save dataframe in ( default: 'latin1' )
    '''
    dest_df = pd.concat(df_batches).reset_index(drop=True)
    dest_df.drop_duplicates(subset=index, inplace=True)
    dest_df.to_csv(path_to_dest, encoding=encoding, index=False)

