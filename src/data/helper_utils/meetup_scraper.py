from __future__ import print_function
import requests, pdb
from time import sleep

'''internal method to make api calls'''
def _make_api_call(url):
    sleep(2) #slow down the requests to stay within the request rate limit
    res = requests.get(url)
    if res.status_code == requests.codes.ok:
       return res.json(), res.headers

    return None

def fetch_topics(url):
    payload, _ = _make_api_call(url)
    if payload != None: 
        print(len(payload))

def fetch_events(url, data):
    if data is None:
        data = [] 

    payload, res_headers = _make_api_call(url)
    if payload != None and len(payload) > 0:
        data += payload

        if 'Link' in  res_headers: 
            next_url = res_headers['Link'].split('<')[1].split('>')[0]
            data = fetch_events(next_url, data)
        else:
            return data

    #  if len(data) == 0: 
        #  print('Something went wrong') 
    return data

def filter_events(events, prop_list):
    filtered_events = []
    for i in range(len(events)):
        prop_subset = { prop: events[i].get(prop, None) for prop in prop_list }
        filtered_events.append(prop_subset)
    return filtered_events

if __name__ == '__main__':
    #  topic_url = "https://api.meetup.com/find/topic_categories?sig_id=236782612&sig=b0d7c90b968372273bf1ea8f769992884bba46d6"
    #  fetch_topics(topic_url)
    event_url = "https://api.meetup.com/find/events?photo-host=public&sig_id=236706760&radius=smart&fields=group&lon=-96.1464161&lat=32.0175481667&sig=3910ed3f0ba3b61ec56fa9af024c8e39136e92e3"
    events = fetch_events(event_url, None)
    filtered_events = filter_events(events, [ 'group' ])
    pdb.set_trace()
