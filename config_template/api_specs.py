props_for = { 
    'locations': {
        'City': 'city',
        'Country': 'localized_country_name', 
        'State': 'state', 
        'ZipCode': 'zip', 
        'Latitude': 'lat',
        'Longitude': 'lon'
    },
    'groups': {
        'only': [ 'id', 'plain_text_description', 'next_event.yes_rsvp_count',
                    'last_event.yes_rsvp_count' ],
        'fields': [ 'plain_text_description', 'last_event' ]
    },
    'events':{
        'topics': {
            'only': [ 'id', 'time',  'group.id', 'yes_rsvp_count' ],
            'fields': [ ]
        },
        'attendance': {
            'only': [ 'id', 'time', 'venue.id', 'venue.zip', 'status', 'rsvp_limit', 'yes_rsvp' ],
            'fields': [ ]
        } 
    }
} 
