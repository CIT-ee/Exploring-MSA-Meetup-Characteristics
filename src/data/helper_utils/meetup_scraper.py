from __future__ import print_function
import os, requests, pdb
from time import sleep


def _throttle_request_rate_by(header):
    num_req_remaining = int(header['X-RateLimit-Remaining'])
    time_to_ratelimit_reset = int(header['X-RateLimit-Reset'])
    if num_req_remaining == 0:
        throttle_for = time_to_ratelimit_reset + 1
    else:
        throttle_for = round((1. * time_to_ratelimit_reset)/num_req_remaining, 3)
    return throttle_for

def _make_api_call(url):
    '''Make a request to the API endpoint.
    
    Keyword arguments:
    url -- the url to make the request to (default None)
    '''

    res = requests.get(url) #fetch the response

    #  make sure that request rates don't go over limit
    #  if one exists
    if 'X-RateLimit-Limit' in res.headers.keys():
        pause_time = _throttle_request_rate_by(res.headers)
    else:
        pause_time = 0

    sleep(pause_time) 

    if res.status_code == 401:
        print('Got 401 status code')
        pdb.set_trace() #  TODO: deal with 401 errors
        
    elif res.status_code == 429:
        #  TODO: deal with when api warns of request 
        #  rate limit overflow
        print('Got 429 status code')
        pdb.set_trace()

    # make sure the server responded with OK status
    elif res.status_code == requests.codes.ok:
        return res.json(), res.headers
    
    # default value to return to indicate something went wrong
    return None

def fetch_paginated_data(url, data):
    '''Scrape an endpoint of the Meetup API that supports Link Header Pagination.

    Meetup API provides response data pagination on these endpoints. Therefore, to
    get all the relevant metadata, the next page's url is parsed from the headers and
    the function is called recursively until the end of the results is reached.

    Keyword arguments:
    url -- the api endpoint to hit (default None)
    data -- the list of response payloads in json (default [])
    '''
    if data is None:
        data = [] # initialize the data for first time method is called

    payload, res_headers = _make_api_call(url)
    #  pdb.set_trace()

    #  continue hitting endpoint only if something is 
    #  returned in response payload
    if payload is not None:
        data = data + payload if len(payload) > 0 else data

        #  parse the next url from the Link attribute in response headers
        if 'Link' in  res_headers: 
            next_url = res_headers['Link'].split('<')[1].split('>')[0]
            data = fetch_paginated_data(next_url, data)
    else:
        #  throttle request_rate
        pass

    return data

def get_chkpnt(path_to_chkpnts):
    assert os.path.exists(path_to_chkpnts), \
            "Sorry there is no checkpoint folder at {}".format(path_to_chkpnts)
    checkpoints = [ os.path.join(path_to_chkpnts, fname) for fname in os.listdir(path_to_chkpnts) ]
    latest_chkpnt = max(checkpoints, key=os.path.getctime)
    #  TODO: figure out how to parse out the numbers
    num_loc, num_cities =latest_chkpnt.split('.')[0].split('_')[-2:]
    return int(num_cities) + 1, int(num_loc) + 1, latest_chkpnt

def filter_events(events, prop_list):
    '''Filter the events to cherry pick only the 'interesting' properties. 
    
    Keyword arguments:
    events -- list of event metadata dictionaries (default None)
    prop_list -- list of properties we are interested in (default None)
    '''
    filtered_events = []

    for i in range(len(events)):
        #  cherry pick the interesting properties and store them in a new dict
        prop_subset = { prop: events[i].get(prop, None) for prop in prop_list }
        filtered_events.append(prop_subset)

    return filtered_events

if __name__ == '__main__':
    '''Test script functionality with code stub'''
    event_url = "https://api.meetup.com/find/events?photo-host=public&sig_id=236706760&radius=smart&fields=group&lon=-96.1464161&lat=32.0175481667&sig=3910ed3f0ba3b61ec56fa9af024c8e39136e92e3"
    events = fetch_paginated_data(event_url, None)
    filtered_events = filter_events(events, [ 'group' ])
