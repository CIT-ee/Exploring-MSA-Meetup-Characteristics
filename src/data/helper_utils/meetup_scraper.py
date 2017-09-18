from __future__ import print_function
import requests

def fetch_topics(url):
    res = requests.get(url)
    if res.status_code == requests.codes.ok:
        payload = res.json()
        print(len(payload))

if __name__ == '__main__':
    url = "https://api.meetup.com/find/topic_categories?sig_id=236782612&sig=b0d7c90b968372273bf1ea8f769992884bba46d6"
    fetch_topics(url)
