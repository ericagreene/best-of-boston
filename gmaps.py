"""
Reads in a CSV of Best of Boston data and queries the Google Places Text
Search API to augment the data for each establishment.

The input CSV must contain the fields `title` and `address`.
"""
import os
import pandas as pd
import requests
import urllib

API_URL_BASE = 'https://maps.googleapis.com/maps/api/place/textsearch/'

default_top_result = {
    'address': None,
    'lat': None,
    'lng': None,
    'name': None,
    'rating': None,
    'types': None,
    'id': None,
    'place_id': None,
}

def make_maps_query(query):
    # url-encode query
    query = urllib.quote_plus(query)

    API_URL = API_URL_BASE + 'json?key={0}&query={1}'.format(API_KEY, query)

    response = requests.get(API_URL)
    results = response.json()['results']

    if len(results) == 0:
        print 'Unable to get result for {}'.format(query)
        return default_top_result

    top_result = response.json()['results'][0]
    return {
        'address': top_result.get('formatted_address'),
        'lat': top_result.get('geometry').get('location').get('lat'),
        'lng': top_result.get('geometry').get('location').get('lng'),
        'name': top_result.get('name'),
        'rating': top_result.get('rating'),
        'types': ','.join(top_result.get('types')),
        'id': top_result.get('id'),
        'place_id': top_result.get('place_id'),
    }


if __name__ == "__main__":
    # Grab API KEY from environment variable
    API_KEY = os.environ.get('API_KEY')

    if API_KEY is None:
        print('Error: no API_KEY env variable set')
        exit(1)

    # load scraped bob data
    df_bob = pd.read_csv('bob_data.csv')

    bob_maps_data = []
    bad_queries = []

    for i,row in df_bob.iterrows():
        query = '{0} {1} {2}'.format(row['title'], row['address'], row['neighborhood'])

        if query in bad_queries:
            top_result = default_top_result
        else:
            # Call API
            top_result = make_maps_query(query)

        if top_result['address'] is None:
            bad_queries += query

        bob_maps_data.append({
            'address': top_result['address'],
            'lat': top_result['lat'],
            'lng': top_result['lng'],
            'name': top_result['name'],
            'rating': top_result['rating'],
            'types': top_result['types'],
            'id': top_result['id'],
            'place_id': top_result['place_id'],
            'url': row['url'],
            'year': row['year'],
            'title': row['title'],
            'description': row['description'],
            'address': row['address'],
            'neighborhood': row['neighborhood'],
            'phone': row['phone'],
            'website': row['website'],
            'category': row['category'],
            'query': query,
        })

    df_bob_maps = pd.DataFrame.from_dict(bob_maps_data)

    df_bob_maps.to_csv('bob_maps.csv', encoding='utf-8')
