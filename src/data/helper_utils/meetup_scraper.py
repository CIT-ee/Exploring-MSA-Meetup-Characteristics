from __future__ import print_function
import requests, pdb
from time import sleep

def _make_api_call(url):
    '''Make a request to the API endpoint.
    
    Keyword arguments:
    url -- the url to make the request to (default None)
    '''
    sleep(1) # to make sure that we dont go above the request rate limit

    res = requests.get(url) #fetch the response

    # make sure the server responded with OK status
    if res.status_code == requests.codes.ok:
       return res.json(), res.headers

    # default value to return to indicate something went wrong
    return None

def fetch_events(url, data):
    '''Scrape the 'find/events' endpoint of the Meetup API.

    Meetup API provides pagination on this endpoint. Therefore, to get all
    the relevant events, the next page's url is parsed from the headers and
    the function is called recursively until the end of the results is reached.

    Keyword arguments:
    url -- the api endpoint to hit (default None)
    data -- the list of response payloads in json (default [])
    '''
    if data is None:
        data = [] # initialize the data for first time method is called

    payload, res_headers = _make_api_call(url)

    #  continue hitting endpoint only if something is 
    #  returned in response payload
    if payload != None and len(payload) > 0:
        data += payload

        #  parse the next url from the Link attribute in response headers
        if 'Link' in  res_headers: 
            next_url = res_headers['Link'].split('<')[1].split('>')[0]
            data = fetch_events(next_url, data)

    return data

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
    events = fetch_events(event_url, None)
    filtered_events = filter_events(events, [ 'group' ])
