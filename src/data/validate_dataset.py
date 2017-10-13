import pandas as pd, os, pdb, sys

sys.path.insert(0, os.environ['PROJECT_PATH'])

from config.resources import path_to

def _is_valid_city(x, city_list):
    '''check if city identifier associated with the location is 
    valid or not.
    
    Keyword arguments:
    x -- the city identifier (default: None)
    city_list -- list of valid cities (default: []) 
    '''
    return ", ".join(x) in city_list

def _clean_place_names(x):
    '''remove filler words from the city name'''
    filler_words = ['city', 'town', 'CDP']
    word_ls = x.split(',')[0].split() + [ x.split()[-1] ]
    return ", ".join( [ w for w in word_ls if w not in filler_words ] )

def validate_cities(path_to_src, path_to_ref):
    '''check how many meetup cities are incorporated places
    and label the associated locations (true/false) if not all
    of them are.
    
    Keyword arguments:
    path_to_src -- path to the dataset we are interested in 
                    validating (default: None)
    path_to_ref -- path to the dataset that serves as the litmus 
                    test (default: None)'''
    locations_df = pd.read_csv(path_to_src, encoding='latin1')

    #  stitch together the city and state names for a unique identifier
    #  then get a list of these unique identifiers
    meetup_cities = locations_df[['City', 'State']].apply( lambda x: ", ".join(x) , axis=1)
    unique_meetup_cities = set(meetup_cities.tolist())


    #  make sure to mark all empty like strings as NA 
    #  and drop records if 'Place Name 2014' column has NA
    places_df = pd.read_csv(path_to_ref, header=1, na_values=' ', encoding='latin1')
    places_df.dropna(subset=['Place Name 2014'], inplace=True)

    #  to match the unique identifiers obtained from meetups dataframe
    #  above, remove filler words like 'city' from the place names 
    #  in the places dataframe
    cleaned_place_names = places_df['Place Name 2014'].apply( lambda x: _clean_place_names(x) )
    unique_places = set(cleaned_place_names.tolist())

    #  find intersection of incorporated city/place names in either list
    valid_cities = unique_places & unique_meetup_cities
    print('\nFound {} incorporated cities out of {} meetups, checked against {} `places`'.format(len(valid_cities), len(unique_meetup_cities), len(unique_places)))

    #  in case the meetup cities are not a subset (proper or otherwise)
    #  of the 'places', label the locations associated with 'incorporated cities'
    if len(valid_cities) < len(unique_places):
        print('\nLabelling meetup locations as incorporated or not. Please wait ..')
        locations_df['Is_Incorporated'] = locations_df[['City', 'State']].apply( lambda x: _mark_valid_cities(x, valid_cities), axis=1 )
        print('Done!')

    valid_locations_df = locations_df[locations_df['Is_Incorporated']]
    print('\nFound {} out of {} meetup locations associated with incorporated cities'.format(valid_locations_df.shape[0], locations_df.shape[0]))

    #  commit the changes made to the meetup cities dataset
    print('\nSaving changes. Please wait ..')
    locations_df.to_csv(path_to_src, index=False, encoding='latin1')
    print('Done!')

if __name__ == '__main__':
    '''stub to test the script'''
    validate_cities(path_to['meetup_locations'], path_to['incorporated_places'])
    pass
