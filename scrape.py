"""

Output:

'url', 'year', 'title', 'description', 'address', 'neighborhood', 'phone', 'website'

TODO:
  * Fix parsing errors
  * Follow 2nd category pages
  * Add other themes
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os.path
import re
import requests


from bs4 import BeautifulSoup
import pandas as pd

YEAR_URL = 'https://www.bostonmagazine.com/best-of-boston/2017/'
CATEGORY = 'https://www.bostonmagazine.com/best-of-boston/2017/category/2017-restaurants-food/'
AWARD_URL = 'https://www.bostonmagazine.com/best-of-boston/2017/award/beer-bar/'

COLUMNS=['url', 'year', 'title', 'description', 'address', 'neighborhood', 'phone', 'website', 'category']

def clean_url():
    pass

def clean_spaces(text):
    return text.replace('\n', ' ').replace('\t','')

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

    # Check for next page URLs, then don't try to parse. For example,
    # '/best-of-boston/2017/award/new-restaurant/page/2/'
    next_page_regex = re.compile('.*/page/[0-9]+/*')
    if re.match(next_page_regex, url) != None:
        return

    # category
    category = soup.findAll('h2', {'class': 'thin-line'})[0].text
    category = ' '.join(clean_spaces(category).split(' ')[1:])

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
        'category': category,
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

    if type == 'category':
        path = 'data/{0}_{1}_{2}.html'.format(type, url.split('/')[-1], url.split('/')[-2])
    else:
        path = 'data/{0}_{1}.html'.format(type, url.split('/')[-2])

    # If we already have the HTML for the page, don't scrape it again
    if os.path.isfile(path):
        #print('skipping {}'.format(path))
        return path

    print('scraping', path)

    # TODO: try / catch
    response = requests.get(url)

    with open(path, 'w') as f:
        f.write(response.text.encode('utf-8'))

    return path

def extract_data_from_category(category_html):
    '''
    Given HTML from a category page like (e.g. /best-of-boston/2017/award/beer-bar/)
    returns a DataFrame with the information from all the winners in that category
    over the years.
    '''
    urls = extract_urls_from_category_page(category_html)

    # Scrape pages for all URLs and save HTML files to disk
    paths = []
    for u in urls:
        path = scrape_if_necessary(u, 'business')
        paths.append(path)

    # Read all business HTML files from disk and extra data

    df_category = pd.DataFrame(columns=COLUMNS)

    for p in paths:
        business_html = open(p, 'r')

        try:
            meta = extract_meta_from_business_page(business_html)
            print(meta['url'])

            df_business = pd.DataFrame(data=meta, columns=COLUMNS, index=[0])
            df_category = df_category.append(df_business)
        except:
            print('Error: unable to parse {0}'.format(p))


    # Write parsed data to CSV
    return df_category

def main():
    restaurant_html = open('data/theme_restaurants.html', 'r')
    soup = BeautifulSoup(restaurant_html, 'html.parser')

    # Extract all URLs for category pages, e.g. list of Best Beer Bars
    category_url_regex = re.compile('.*/best-of-boston/[0-9]+/award/.*')
    category_urls = [l['href'] for l in soup.findAll('a',  href=category_url_regex)]
    category_urls = list(set(category_urls))

    # Scrape all category pages
    theme_paths = []
    for url in category_urls:
        path = scrape_if_necessary(url, 'category')
        theme_paths.append(path)

    df_theme = pd.DataFrame(columns=COLUMNS)

    for path in theme_paths:
        category_html = open(path, 'r')
        df_category = extract_data_from_category(category_html)
        df_theme = df_theme.append(df_category)

    df_theme.to_csv('bob_data.csv', encoding='utf-8')

if __name__ == "__main__":
    main()
