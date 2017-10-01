#!/usr/bin/env python3
# I'm going to have to multiprocess these at some point.
# The pipeline will be:
#     process city:
#         get zip
#         get id
#         ...
#     Farm out api calls to other processes
#     Collect the results
#     display the page
# I'm going to worry about threading when I've got at least a few api's done
# use concurrent.futures for this
# All of these return None on failure. I check for none in results.html
# I should think about separating the I/O from the logic here

import os
from collections import namedtuple
import datetime
import json
# import pprint

import tweepy
import pyowm
import geocoder
import requests
import xml.etree.ElementTree as ET
# pretty printing
from xml.dom import minidom


def pretty_print_xml(xml_string):
    reparsed = minidom.parseString(xml_string)
    print(reparsed.toprettyxml(indent='\t'))


# Moved from config because I'm only going to use these here and
# I want to mulitprocess this file
try:
    # Current Weather: done
    # Can also get historical data and make a graph?
    KEY_OPENWEATHERMAP = os.environ['KEY_OPENWEATHERMAP']
    # Not done
    KEY_GOOGLEDEVCONSOLE = os.environ['KEY_GOOGLEDEVCONSOLE']
    # Country code (ISO 3166) for US: US
    # Somewhat done
    KEY_NUMBEO = os.environ['KEY_NUMBEO']
    # Can get School overview and Schools. Need to format the CSS
    # Need to attach a database to this so I can see if cities are in it
    # I'm not going to have time to mess with this until after Monday
    KEY_GREATSCHOOLS = os.environ['KEY_GREATSCHOOLS']
    # Crime. THis api is not very complete...
    KEY_XMASHAPE = os.environ['KEY_XMASHAPE']
    KEY_ZILLOW = os.environ['KEY_ZILLOW']
    # Twitter thingies
    KEY_TWIT_CON_KEY = os.environ['KEY_TWIT_CON_KEY']
    KEY_TWIT_CON_SECRET = os.environ['KEY_TWIT_CON_SECRET']
    KEY_TWIT_ACC_TOK = os.environ['KEY_TWIT_ACC_TOK']
    KEY_TWIT_ACC_KEY = os.environ['KEY_TWIT_ACC_KEY']
except KeyError as e:
    raise SystemExit("Load API keys into shell variables: `source api_keys.sh`. Missing key: " + str(e))

# namedtuples: These are the boundaries between my API code and my templating code
Weather = namedtuple('Weather', ['temperature', 'wind_speed', 'humidity'])
SchoolOverview = namedtuple('SchoolOverview', ['total_schools', 'elementary_schools', 'middle_schools',
                                               'high_schools', 'public_schools', 'charter_schools',
                                               'private_schools'])
School = namedtuple('School', ['name', 'type', 'grade_range', 'enrollment', 'district', 'address', 'phone',
                               'fax', 'website', 'overview_link', 'ratings_link', 'reviews_link'])
LatLng = namedtuple('LatLng', ['lat', 'lng'])

Crime = namedtuple('Crime', ['datetime', 'description'])

RateSummaryDay = namedtuple('RateSummaryDay', ['thirty_year_fixed', 'fifteenn_year_fixed', 'five_one_ARM'])
RateSummaryWeek = namedtuple('RateSummaryWeek', ['thirty_year_fixed', 'fifteenn_year_fixed', 'five_one_ARM'])


def find_or_none(tag, sub_tag):
    try:
        item = tag.find(sub_tag).text
    except AttributeError:
        return None
    else:
        return item


def get_latlng(state, city):
    g = geocoder.google(city + ', ' + state)
    lat, lng = g.latlng
    return LatLng(lat, lng)


def get_weather(city):
    # TODO: get this to do historical stuff
    owm = pyowm.OWM(KEY_OPENWEATHERMAP)
    observation = owm.weather_at_place(city + ',us')
    if observation:
        w = observation.get_weather()
        return Weather(w.get_temperature('fahrenheit')['temp'],
                       w.get_wind()['speed'],
                       w.get_humidity())
    return None


def get_school_overview(state, city):
    city = city.replace(' ', '-')
    state = state.upper()
    url_string = 'http://api.greatschools.org/cities/{state}/{city}?key={key}'
    url_string = url_string.format(state=state,
                                   city=city,
                                   key=KEY_GREATSCHOOLS)
    result = requests.get(url_string)
    # returns 0's for everything on failure
    root = ET.fromstring(result.text)
    # for child in root:
    #     print(child.tag, child.text)
    if root.find('totalSchools').text == 0:
        return None
    return SchoolOverview(find_or_none(root, 'totalSchools'),
                          find_or_none(root, 'elementarySchools'),
                          find_or_none(root, 'middleSchools'),
                          find_or_none(root, 'highSchools'),
                          find_or_none(root, 'publicSchools'),
                          find_or_none(root, 'charterSchools'),
                          find_or_none(root, 'privateSchools'))


def get_schools_generator(state, city):
    city = city.replace(' ', '-')
    state = state.upper()
    url_string = 'http://api.greatschools.org/schools/{state}/{city}?key={key}'
    url_string = url_string.format(state=state,
                                   city=city,
                                   key=KEY_GREATSCHOOLS)
    result = requests.get(url_string)
    # returns 0's for everything on failure
    try:
        root = ET.fromstring(result.text)
    except ET.ParseError:
        return None
    print(root.tag)
    for child in root:
        yield School(find_or_none(child, 'name'),
                     find_or_none(child, 'type'),
                     find_or_none(child, 'gradeRange'),
                     find_or_none(child, 'enrollment'),
                     find_or_none(child, 'district'),
                     find_or_none(child, 'address'),
                     find_or_none(child, 'phone'),
                     find_or_none(child, 'fax'),
                     find_or_none(child, 'website'),
                     find_or_none(child, 'overviewLink'),
                     find_or_none(child, 'ratingsLink'),
                     find_or_none(child, 'reviewsLink'))


# TODO: this only works for some cities (San-Francisco, CA)
def get_crimes_generator(state, city):
    lat, lng = get_latlng(state, city)
    # lat = '37.757815'
    # lng = '-122.5076392'
    today = datetime.datetime.today()
    today_str = today.strftime('%m %d %Y').replace(' ', '%2F')
    time_delta = datetime.timedelta(7)
    three_months_ago_str = (today - time_delta).strftime('%m %d %Y').replace(' ', '%2F')
    payload = dict(lat=lat, long=lng, startdate=three_months_ago_str, enddate=today_str)
    payload = '?enddate={end_date}&lat={lat}&long={lng}&startdate={start_date}'.format(end_date=today_str,
                                                                                       lat=lat,
                                                                                       lng=lng,
                                                                                       start_date=three_months_ago_str)
    # url_string = 'https://jgentes-Crime-Data-v1.p.mashape.com/crime?enddate=9%2F25%2F2015&lat=37.757815&long=-122.5076392&startdate=9%2F19%2F2015'
    url_string = 'https://jgentes-Crime-Data-v1.p.mashape.com/crime' + payload
    headers = {'X-Mashape-Key': KEY_XMASHAPE, 'Accept': 'application/json'}
    result = requests.get(url_string, headers=headers)
    # print(result.request.headers)
    # print(result.request.url)
    crimes = json.loads(result.text)
    if not crimes:
        return None
    for crime in crimes:
        yield Crime(crime['datetime'], crime['description'])


def get_zillow():
    url = 'http://www.zillow.com/webservice/GetZestimate.htm?zws-id={KEY_ZILLOW}&zpid=48749425'.format(KEY_ZILLOW=KEY_ZILLOW)
    result = requests.get(url)
    print(KEY_ZILLOW)
    print(result.request.url)
    print(result.text)

RateSummaryDay = namedtuple('RateSummaryDay', ['thirty_year_fixed', 'fifteen_year_fixed', 'five_one_ARM'])
RateSummaryWeek = namedtuple('RateSummaryWeek', ['thirty_year_fixed', 'fifteen_year_fixed', 'five_one_ARM'])


def get_zillow_rate_summary_day(state):
    state = state.upper()
    url = 'http://www.zillow.com/webservice/GetRateSummary.htm?zws-id={KEY_ZILLOW}&state={state}'.format(KEY_ZILLOW=KEY_ZILLOW,
                                                                                                         state=state)
    print(url)
    result = requests.get(url)
    root = ET.fromstring(result.text)
    # i = root.find('message').find('response').find('today')
    i = root.find('response').find('today')
    for child in i:
        if child.get('loanType') == 'thirtyYearFixed':
            thirty_year_fixed = child.text
        elif child.get('loanType') == 'fifteenYearFixed':
            fifteen_year_fixed = child.text
        elif child.get('loanType') == 'fiveOneARM':
            five_one_ARM = child.text
    return RateSummaryDay(thirty_year_fixed, fifteen_year_fixed, five_one_ARM)


def get_zillow_rate_summary_week(state):
    state = state.upper()
    url = 'http://www.zillow.com/webservice/GetRateSummary.htm?zws-id={KEY_ZILLOW}&state={state}'.format(KEY_ZILLOW=KEY_ZILLOW,
                                                                                                         state=state)
    print(url)
    result = requests.get(url)
    root = ET.fromstring(result.text)
    # i = root.find('message').find('response').find('today')
    i = root.find('response').find('lastWeek')
    for child in i:
        if child.get('loanType') == 'thirtyYearFixed':
            thirty_year_fixed = child.text
        elif child.get('loanType') == 'fifteenYearFixed':
            fifteen_year_fixed = child.text
        elif child.get('loanType') == 'fiveOneARM':
            five_one_ARM = child.text
    return RateSummaryWeek(thirty_year_fixed, fifteen_year_fixed, five_one_ARM)

# RegionChart = namedtuple('RegionChart', ['chart_url', 'city_link', 'local_link', 'for_sale_link',
#                                          'for_sale_by_owner_link'])
RegionChart = namedtuple('RegionChart', 'chart_url')


def get_region_chart(state, city):
    state = state.upper()
    city = city.replace(' ', '+')
    url = "http://www.zillow.com/webservice/GetRegionChart.htm?zws-id={KEY_ZILLOW}&city={city}&state={state}&unit-type=percent&width=300&height=150".format(KEY_ZILLOW=KEY_ZILLOW, city=city, state=state)
    # print(url)
    result = requests.get(url)
    root = ET.fromstring(result.text)
    try:
        img = root.find('response').find('url').text
    except AttributeError as e:
        # pretty_print_xml(result.text)
        # print(str(e))
        return None
    else:
        return RegionChart(img)


Tweet = namedtuple('Tweet', 'text')


def get_tweets_generator(city, count=15):
    # # NOTE: returning None here till I can find/create Twitter creds
    # return None
    city = city.replace(' ', '-')
    city = city.lower()
    print('city: ', city)
    auth = tweepy.AppAuthHandler(KEY_TWIT_CON_KEY, KEY_TWIT_CON_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    if not api:
        return None
    new_tweets = api.search(q=city, count=count)
    for tweet in new_tweets:
        yield Tweet(tweet.text)


if __name__ == '__main__':
    # test_get_weather()
    # print(get_school_overview('AR', 'North Little Rock'))
    # for school in get_schools_generator('CR', 'North Little Rock'):
    #     print(school)
    # print(get_latlng('AR', 'North Little Rock'))
    print(list((get_crimes_generator('Ar', 'North Little Rock'))))
    # for crime in get_crimes_generator('CA', 'San-Francisco'):
        # print(crime)
    # get_zillow()
    # print(get_zillow_rate_summary_day('AR'))
    # print(get_region_chart('WA', 'Seattle'))
    # print(get_region_chart('LR', 'Little Rock'))
