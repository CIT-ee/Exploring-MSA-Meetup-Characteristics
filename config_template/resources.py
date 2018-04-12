import os
PATH_TO_PROJECT = os.environ['PROJECT_PATH']

path_to = {
    'chkpnts': os.path.join(os.environ['DATA_PATH'], 'raw', '{endpoint}', 'chkpnts'), 
    'msa_codes': os.path.join(os.environ['DATA_PATH'], 'external', 'CBSA2015.csv'),
    'cities': os.path.join(os.environ['DATA_PATH'], 'external', 'Cities_and_Towns_NTAD.csv'),
    'meetup_locations': os.path.join(os.environ['DATA_PATH'], 'interim', 'locations', 'meetup_locations.csv'),
    'meetup_locations_batch': os.path.join(os.environ['DATA_PATH'], 'interim', 'locations', 'batches', 'meetup_locations_{}.csv'),
    'incorporated_places': os.path.join(os.environ['DATA_PATH'], 'external', 'Places-to-CBSA15_geocorr14.csv'),
    'scraped_endpoint': os.path.join(os.environ['DATA_PATH'], 'raw', '{endpoint}', '{query}', 'meetup_{endpoint}.csv'),
    'scraped_batch': os.path.join(os.environ['DATA_PATH'], 'raw', '{endpoint}', '{query}', 'batches', 'meetup_{endpoint}_{idx}.csv'),
    'with_msa_endpoint': os.path.join(os.environ['DATA_PATH'], 'raw', '{endpoint}', '{query}', 'meetup_{endpoint}_with_msa.csv'),
    'with_msa_batch': os.path.join(os.environ['DATA_PATH'], 'raw', '{endpoint}', '{query}', 'batches', 'meetup_{endpoint}_{idx}_with_msa.csv'),
}
