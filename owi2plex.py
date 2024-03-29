#!/usr/bin/env python3
import click
import requests
import re
import collections
import yaml
import os
import html
import codecs
import logging

from lxml import etree
from datetime import datetime, timedelta, time


__version__ = ''
exec(open(os.path.dirname(os.path.realpath(__file__))+'/version.py').read())
logger = None


def unescape(text):
    """
    Safe check of the existence of the unescape function as the future module
    doesn't appear to have it yet.

    https://github.com/PythonCharmers/python-future/issues/247

    This function also replaces control characters for XML compatibility
    """
    try:
        text = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', text)
        return html.unescape(text)
    except:
        return text


def getAPIRoot(username, password, host, port):
    """
    Simple function to form the url of the OpenWebif server.
    More info at:
    
    https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/wiki/OpenWebif-API-documentation
    """
    if username:
        url = 'http://{}:{}@{}:{}'.format(
                username, password, host, port)
    else:
        url = 'http://{}:{}'.format(host, port)
    return url


def getBouquets(bouquet, api_root_url, list_bouquets):
    """
    Function to get the list of bouquets from the OpenWebif API
    
    return_type: dict
    return_model:
        {
            "bouquet_name_1": "sRef_1",
            ...
            "bouquet_name_n": "sRef_n",
        }
    """
    global logger
    result = collections.OrderedDict()
    url = '{}/api/bouquets'.format(api_root_url)
    try:
        bouquets_data = requests.get(url)
        bouquets = bouquets_data.json()['bouquets']
        for b in bouquets:
            if list_bouquets:
                logger.info(u"Found bouquet: {}".format(b[1]))
            if b[1] == bouquet or not bouquet:
                result[b[1]] = b[0]
    except Exception:
        raise
    return result


def getBouquetsServices(bouquets, api_root_url):
    """
    Function to return the list of services (channels) for each bouquet in the
    bouquets param

    params:
        - boutquets: [bouquet_obj_1, bouquet_obj_2, ...]
        - api_root_url: Root URL of the OpenWebif server
    returns:
        - type: dict
        - model:
            {
                "bouquet_name_1": [svc_1_obj, svc_2_obj, ..., svc_n_obj],
                ...
                "bouquet_name_n": [svc_1_obj, svc_2_obj, ..., svc_n_obj]
            }
    """
    services = collections.OrderedDict()
    try:
        for bouquet_name, bouquet_svc_ref in bouquets.items():
            url = '{}/api/getservices?sRef={}'.format(api_root_url, bouquet_svc_ref)
            services_data = requests.get(url)
            services[bouquet_name] = services_data.json()['services']
    except Exception:
        raise
    return services


def getEPGs(bouquets_services, api_root_url):
    """
    Function to get the EPGs for the services in the bouquet_services param.

    params:
        - bouquet_services: [svc_obj_1, svc_obj_2, ...]
        - api_root_url: Root URL of the OpenWebif server
    returns:
        - type: dict
        - model:
            {
                "program_id": [ event_obj_1, event_obj_2, ...],
                ...,
                "program_id": [ event_obj_1, event_obj_2, ...]
            }
    """
    global logger
    epg = {}
    for _, services in bouquets_services.items():
        for service in services:
            if service['pos']:
                url = u'{}/api/epgservice?sRef={}'.format(api_root_url, service['servicereference'])
                debug_message = u"Getting EPG for service {}. {} ({}) from {}".format(
                    service['pos'], service['servicename'], service['program'],
                    url)
                logger.info(debug_message)
                try:
                    service_epg_data = requests.get(url)
                    epg[service['program']] = service_epg_data.json()['events']
                except Exception:
                    raise
    return epg


def getOffset(api_root_url):
    global logger
    now = datetime.timestamp(datetime.now())
    offset = (datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)).total_seconds()
    hours = round(offset / 3600)
    minutes = (offset - (hours * 3600))
    tzo = "{:+05}".format(int(hours * 100 + (round(minutes / 900) * 900 / 60)))

    logger.info("Setting TZ Offset from UTC to {}".format(tzo))
    return tzo


def addChannels2XML(xmltv, bouquets_services, epg, api_root_url, continuous_numbering):
    """
    Function to add the list of services/channels to the resultant XML object.

    returns:
        - type: lxml.etree
    """
    continuous_service_position = 1
    for _, services in bouquets_services.items():
        for service in services:
            if service['pos']:
                channel = etree.SubElement(xmltv, 'channel')
                channel.attrib['id'] = '{}'.format(service['program'])
                etree.SubElement(channel, 'display-name').text = unescape(service['servicename'])
                if (continuous_numbering == True):
                    etree.SubElement(channel, 'display-name').text = str(continuous_service_position)
                else:
                    etree.SubElement(channel, 'display-name').text = str(service['pos'])
                if epg[service['program']]:
                    first_event = epg[service['program']][0]
                    channel_picon = etree.SubElement(channel, 'icon')
                    channel_picon.attrib['src'] = '{}{}'.format(api_root_url, first_event['picon'])
            continuous_service_position += 1
    return xmltv


def addCategories2Programme(title, programme, event, overrides):
    """
    Function to add the catergories to a program. Returns the XML program object
    with the cateogry added.

    returns:
        - type: lxml.etree
    """
    category_overrides = []
    categories = re.search(r'^\[(?P<C1>[\w\s]+)[\.\s]*(?P<C2>[\w\s]+)*\]', event['shortdesc'])

    if overrides:
        for pattern, override_categories in overrides.items():
            if pattern in title.upper():
                for category in override_categories:
                    category_overrides.append(category) 

    if len(category_overrides) > 0:
        for cat_override in category_overrides:
            programme_category = etree.SubElement(programme, 'category')
            programme_category.attrib['lang'] = 'en'
            programme_category.text = '{}'.format(cat_override)
    elif categories:
        for category in categories.groupdict().values(): 
            if category:
                programme_category = etree.SubElement(programme, 'category')
                programme_category.attrib['lang'] = 'en'
                programme_category.text = '{}'.format(category)

    return programme

def parseSEP(text):
    """
    Function to parse the Seasson.Episode.Part numbers
    """ 
    global logger
    logger.debug("ParsingSEP: {}".format(text))
    S = ''
    E = ''
    P = ''
    is_a_match = True
    match = None
    is_premiere = False

    c4_style = re.search(r'(?:S(?P<S>\d+)(?:\/|\s)*)?(?:Ep|E)\s*(?P<E>\d+)(?:\/(?P<P>\d+))?', text)
    bbc_style = re.search(r'^(?P<E>\d+)\/(?P<P>\d+)\.', text)
    if bbc_style:
        match = bbc_style
    elif c4_style:
        match = c4_style
    else:
        is_a_match = False

    if match:
        group_names = match.groupdict().keys()
        if 'S' in group_names:
            S = '{}'.format(int(match.group('S')) - 1 if match.group('S') else '')
        else:
            S ='0'
        if 'E' in group_names:
            E = '{}'.format(int(match.group('E')) - 1 if match.group('E') else '')
            if E == '1' or E == '0':
                is_premiere = True
        if 'P' in group_names:
            P = '{}'.format(int(match.group('P')) - 1 if match.group('P') else '')
    logger.debug("ParseSEP ==>{}: {}.{}.{}".format(is_a_match, S,E,P))    
    return is_a_match, '{}.{}.{}'.format(S, E, P), is_premiere


def addSeriesInfo2Programme(programme, event, air_dt):
    """
    Function to add Information to programs with the Categories Series or Show
    relating to the episode number or original air date.

    returns:
        - type: lxml.etree
    """
    original_air_date = re.search( r'(\d{2})[\/|\.|\-](\d{2})[\/|\.|\-](\d{4})', event['shortdesc'])
    match_epnum, epnum, is_premiere = parseSEP(event['shortdesc'])

    # Don't attempt to put an episode-num to certain categories
    try:
        existing_category = programme.find('category')
        if existing_category.text in ('Movie', 'News'):
            return programme
    except AttributeError:
        pass

    if match_epnum:
        programme_epnum = etree.SubElement(programme, 'episode-num')
        programme_epnum.attrib['system'] = 'xmltv_ns'
        programme_epnum.text = epnum

        # If it hasn't got a category but a epnum then it must be a Series
        if existing_category is None:
            programme_category = etree.SubElement(programme, 'category')
            programme_category.attrib['lang'] = 'en'
            programme_category.text = 'Series'

        # Notes the first screening of a new show.
        if epnum == '1.1.' or epnum == '1.1.1':
            _ = etree.SubElement(programme, 'new')

        # Notes the first screened episode of a new or existing show.
        if is_premiere:
            _ = etree.SubElement(programme, 'premiere')

    if original_air_date:
        programme_epnum = etree.SubElement(programme, 'episode-num')
        programme_epnum.attrib['system'] = 'original-air-date'
        programme_epnum.text = "{}-{}-{}".format(
            original_air_date.group(3),
            original_air_date.group(2),
            original_air_date.group(1))
        try:
            original_air_dt = datetime.strptime(programme_epnum.text, '%Y-%m-%d')
            if air_dt.date() > original_air_dt.date():
                _ = etree.SubElement(programme, 'previously-shown')
        except ValueError as e:
            pass
            # The orinal air date cannot be parse and will therefore be ignored
            
    return programme


def addMovieCredits(programme, event):
    try:
        existing_category = programme.find('category')
        if existing_category.text in ('Movie'):
            cast = event['longdesc'].split('\n', 2)
            if len(cast)>2:
                credits = etree.SubElement(programme, 'credits')
                director = etree.SubElement(credits, 'director')
                director.text = cast[1]
                for cast in cast[2][:-1].split('\n'):
                    actor = etree.SubElement(credits, 'actor')
                    actor.text = cast
    except AttributeError:
        pass
    return programme


def load_overrides(category_override):
    transformed_overrides = None
    if category_override:
        transformed_overrides = {}
        with open(category_override, 'r', encoding="utf-8") as cof:
            try:
                overrides = yaml.safe_load(cof)
                for cat, ltitles in overrides.items():
                    for title in ltitles:
                        if transformed_overrides.get(title.upper(), None):
                            transformed_overrides[title.upper()].append(cat)
                        else: 
                            transformed_overrides[title.upper()] = [cat]
            except yaml.YAMLError:
                raise
    return transformed_overrides


def addEvents2XML(xmltv, epg, tzoffset, category_override):
    """
    Function to add events (programms) to the XMLTV structure.

    returns:
        - type: lxml.etree
    """
    overrides = load_overrides(category_override)

    for service_program, events in epg.items():
        for event in events:
            # Time Calculations and transformations
            start_dt = datetime.fromtimestamp(event['begin_timestamp'])
            start_dt_str = start_dt.strftime("%Y%m%d%H%M%S {}".format(tzoffset))
            end_dt = start_dt + timedelta(minutes=event['duration'])
            end_dt_str = end_dt.strftime("%Y%m%d%H%M%S {}".format(tzoffset))

            programme = etree.SubElement(xmltv, 'programme')
            programme.attrib['channel'] = str(service_program)
            programme.attrib['start'] = start_dt_str
            programme.attrib['stop'] = end_dt_str

            programme_duration = etree.SubElement(programme, 'length')
            programme_duration.attrib['units'] = 'minutes'
            programme_duration.text = str(event['duration'])

            # Get the Description of the program - Assumes English language
            programme_desc = etree.SubElement(programme, 'desc')
            if event['longdesc'] == '':
                programme_desc.text = unescape(event['shortdesc'])
            else:
                programme_desc.text = unescape(event['longdesc'])
                subtitle_first_step = re.sub(r'^(\[.+\]\s*)', '', event['shortdesc'])
                subtitle = re.sub(r'\s*\([SE]\d+.*\)', '', subtitle_first_step)
                if len(subtitle) > 0:
                    programme_subtitle = etree.SubElement(programme, 'sub-title')
                    programme_subtitle.text = unescape(subtitle)
                    programme_subtitle.attrib['lang'] = 'en'
            programme_desc.attrib['lang'] = 'en'
            if event['shortdesc'] == '':
                event['shortdesc'] = event['longdesc']

            # Get the title and remove the word NEW if present 
            title = unescape(event['title'])
            if 'New: ' in title:
                #_ = etree.SubElement(programme, 'premiere')
                title = title.replace('New: ', '')
            programme_title = etree.SubElement(programme, 'title')
            programme_title.text = title 
            programme_title.attrib['lang'] = 'en'

            programme = addCategories2Programme(event['title'], programme, event, overrides)
            programme = addSeriesInfo2Programme(programme, event, start_dt)   
            programme = addMovieCredits(programme, event)         

    return xmltv


def generateXMLTV(bouquets_services, epg, api_root_url, tzoffset,
        continuous_numbering, category_override):
    """
    Function to generate the XMLTV object

    returns:
        - type: string
        - desc: Representation of the XMLTV object as a String.
    """
    global logger
    logger.info(u"Generating XMLTV payload.")
    xmltv = etree.Element('tv')
    xmltv.attrib['generator-info-url'] = 'https://github.com/cvarelaruiz'
    xmltv.attrib['generator-info-name'] = 'OpenWebIf 2 Plex XMLTV'
    xmltv.attrib['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    xmltv = addChannels2XML(xmltv, bouquets_services, epg, api_root_url, continuous_numbering)
    xmltv = addEvents2XML(xmltv, epg, tzoffset, category_override)

    return etree.tostring(xmltv, encoding='unicode', pretty_print=True)


@click.command()
@click.option('-b', '--bouquet', help='The name of the bouquet to parse. If not'
              ' specified parse all bouquets.', type=click.STRING)
@click.option('-u', '--username', help='OpenWebIf username.', type=click.STRING)
@click.option('-p', '--password', help='OpenWebIf password.', type=click.STRING)
@click.option('-h', '--host', help='OpenWebIf host.', default='localhost',
    type=click.STRING)
@click.option('-P', '--port', help='OpenWebIf port.', default=80, type=click.INT)
@click.option('-o', '--output-file', help='Output file.', default='epg.xml',
    type=click.STRING)
@click.option('-c', '--continuous-numbering', help='Continuous numbering across'
              ' bouquets.', is_flag=True)
@click.option('-l', '--list-bouquets', help='Display a list of bouquets.', 
    is_flag=True)
@click.option('-V', '--version', help='Displays the version of the package.',
    is_flag=True)
@click.option('-O', '--category-override', help='Category override YAML file. '
              'See documentation for file format.', type=click.STRING,)
@click.option('-d', '--debug', help='Verbose Debugging.', is_flag=True)
def main(bouquet=None, username=None, password=None, host='localhost', port=80,
    output_file='epg.xmltv', continuous_numbering=False, list_bouquets=False,
    version=False, category_override=None, debug=False):

    # Initialize Debugging
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    log_format = "%(levelname)s %(asctime)s - %(message)s"
    logging.basicConfig(
        filename = "./owi2plex.log",
        filemode = "w",
        format = log_format,
        level = level)
    global logger
    logger = logging.getLogger('OWI2PLEX')

    if version:
        print(u"OWI2PLEX version {}".format(__version__))
        exit(0)

    api_root_url = getAPIRoot(username=username, password=password, host=host, port=port)

    # Retrieve Data from OpenWebIf
    bouquets = getBouquets(bouquet=bouquet, api_root_url=api_root_url,
        list_bouquets=list_bouquets)
    bouquets_services = getBouquetsServices(bouquets=bouquets, api_root_url=api_root_url)
    epg = getEPGs(bouquets_services=bouquets_services, api_root_url=api_root_url)
    tzoffset = getOffset(api_root_url=api_root_url)

    # Generate the XMLTV file 
    xmltv = generateXMLTV(
        bouquets_services, epg, api_root_url, tzoffset, continuous_numbering,
        category_override)
    logger.info(u"Saving XMLTV payload to file {}".format(output_file))
    try:
        with codecs.open(output_file, 'w', 'utf-8-sig') as xmltv_file:
            xmltv_file.write(xmltv)
            logger.info(u"Boom!")
    except Exception:
        logger.error(u"Uh-oh! Something's happened ...")
        raise

if __name__ == '__main__':
    main()
