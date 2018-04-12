## Overview

This directory holds some project wide configuration settings, housed mainly in two python files - *resources.py* and *api_specs.py*.

## Details

* `resources.py`: This script mainly houses a variable called *path_to* which is essentially a dictionary of important filepaths needed in the project. The current structure (as referenced in the source code) looks as below:

    ```json
    "raw_data": "",
    "raw": {
        "chkpnts": {
            "locations": "",
            "events": ""
        }   
    },  
    "meetup_locations": "",
    "meetup_locations_chkpnt": "",
    "meetup_events": {
        "topics": "",
        "attendance": ""
    }
    ```
*  `api_specs.py`: This script houses a dictionary of important metadata about the properties you are interested in scraping from a Meetup API endpoint. Each key on the first level in the dictionary is an alias for the endpoint (*locations* and *events* were used as referenced in the source code). 

    The *locations* key has an dictionary of api endpoint fields where the key is the name of the dataframe column and the value is the field name. 

    The *events* key points to a dictionary of dictionaries wherein each key is an alias to a subcategory of information you are interested in scraping from that endpoint - *topics* and *attendance* are used in the source code. 

    Each of these *sub-category* dictionaries consist of two properties `only` and `fields`, each of which points to a list of field names/keywords. See [Meetup API documentation](https://www.meetup.com/meetup_api/) for information on what keywords to use. A sample structure for the dictionary is shown below:

    ```python
    'locations': {
        'City': 'city',
        'Country': 'localized_country_name', 
        'State': 'state', 
        'ZipCode': 'zip', 
        'Latitude': 'lat',
        'Longitude': 'lon'
    },
    'events':{
        'topics': {
            'only': [ 'id', 'time', 'venue.id', 'venue.zip', 'status', 'group.topics.name' ],
            'fields': [ 'group_topics' ]
        },
        'attendance': {
            'only': [ 'id', 'time', 'venue.id', 'venue.zip', 'status', 'rsvp_limit', 'yes_rsvp' ],
            'fields': [ ]
        } 
    }
    ```
