"""

Output:

award, name, location, year, description, website, number, location
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import argparse
import os.path
import re
import requests


from bs4 import BeautifulSoup
import pandas as pd

YEAR_URL = 'https://www.bostonmagazine.com/best-of-boston/2017/'
CATEGORY = 'https://www.bostonmagazine.com/best-of-boston/2017/category/2017-restaurants-food/'
AWARD_URL = 'https://www.bostonmagazine.com/best-of-boston/2017/award/beer-bar/'

def clean_url():
    pass

def clean_spaces(text):
    return text.replace('\n', '').replace('\t','')

def extract_urls_from_category_page(category_html):
    '''
    Given a string of HTML associated with a Category Page, returns a list of
    URLs of all the Best of Boston Business Pages on the page.
    '''
    soup = BeautifulSoup(category_html, 'html.parser')

    # Extract all links to pages that match the pattern for landing pages for
    # best of boston business
    url_regex = re.compile('.*/best-of-boston/[0-9]+/.*')
    urls = [l['href'] for l in soup.findAll('a',  href=url_regex)]

    # TODO: clean all URLs

    # Remove duplicates
    urls = list(set(urls))

    return urls



def extract_meta_from_business_page(business_html):
    soup = BeautifulSoup(business_html, 'html.parser')

    # url
    url = soup.findAll('link', {'rel': 'canonical'})[0]['href']

    # year
    year = url.split('/')[-3] # HACK, use a regex

    # title
    title = soup.findAll('h3', {'class': 'post-title'})[0].text

    # description
    description = soup.findAll('div', {'class': 'bob-content'})[0].findAll('p')[0].text
    description = clean_spaces(description)

    # meta span
    meta = soup.findAll('div', {'class': 'bm-bob-meta'})[0].text
    meta = clean_spaces(meta)

    address, neighborhood, phone, website = meta.split(',')
    # print('meta:', meta)

    return {
        'url': url,
        'year': year,
        'title': title,
        'description': description,
        'address': address,
        'neighborhood': neighborhood,
        'phone': phone,
        'website': website,
    }

def scrape_if_necessary(url, type):
    '''
    Given a URL and a string associated with the type of page we're scraping,
    checks to see if we already have the HTML associated with the page on disk.
    If not, scrapes the page and saves the HTML to 'data/{type}-{name}.html'

    url: the URL, e.g. 'https://www.bostonmagazine.com/best-of-boston/2008/sunset-grill-tap-5/'
    type: a string corresponding to the type of page being scrapes. Currently one
         of ['business', 'category']
    '''

    if type not in ['business', 'category']:
        print('type supplied to scrape_if_necessary not valid')
        raise ValueError()

    path = 'data/{0}_{1}.html'.format(type, url.split('/')[-2])

    # If we already have the HTML for the page, don't scrape it again
    if os.path.isfile(path):
        print('skipping {}'.format(path))
        return path

    print('scraping', path)

    # TODO: try / catch
    response = requests.get(url)

    with open(path, 'w') as f:
        f.write(response.text.encode('utf-8'))

    return path

def main():

    beer_bar_html = open('data/category_beer-bar.html', 'r')
    urls = extract_urls_from_category_page(beer_bar_html)

    # Scrape pages for all URLs and save HTML files to disk
    paths = []
    for u in urls:
        path = scrape_if_necessary(u, 'business')
        paths.append(path)

    # Read all business HTML files from disk and extra data
    columns=['url', 'year', 'title', 'description', 'address', 'neighborhood', 'phone', 'website']
    df = pd.DataFrame(columns=columns)

    for p in paths:
        business_html = open(p, 'r')

        try:
            meta = extract_meta_from_business_page(business_html)
            df_business = pd.DataFrame(data=meta, columns=columns, index=[0])
            df = df.append(df_business)
        except:
            print('unable to parse {0}'.format(p))


    # Write parsed data to CSV
    df.to_csv('bob_data.csv', encoding='utf-8')
    return

if __name__ == "__main__":
    main()
