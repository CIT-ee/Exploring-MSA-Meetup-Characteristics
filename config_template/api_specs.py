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
        'only': [ 'id', 'category.name', 'created', 'lat', 'link', 'lon', 'members', \
                'name', 'past_event_count', 'status', 'topics.urlkey', 'who', \
                'next_event.yes_rsvp_count', 'last_event.yes_rsvp_count', 'plain_text_description' ],
        'fields': [ 'last_event', 'topics', 'plain_text_description', 'past_event_count' ]
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
