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
        'only': [ 'id', 'name', 'status', 'link', 'created', 'lat', 'lon', 'who', 
                'category.name', 'members', 'past_event_count', 'topics.urlkey' ],
        'fields': [ 'past_event_count', 'topics' ]
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
