#!/usr/bin/env python3
import click
import requests
import html
import re

from lxml import etree
from datetime import datetime, timedelta


def getAPIRoot(username, password, host, port):
    if username:
        url = 'http://{}:{}@{}:{}'.format(
                username, password, host, port)
    else:
        url = 'http://{}:{}'.format(host, port)
    return url


def getBouquets(bouquet, api_root_url, list_bouquets):
    """
    Function to get the list of bouquets
    """
    result = {}
    url = '{}/api/bouquets'.format(api_root_url)
    try:
        bouquets_data = requests.get(url)
        bouquets = bouquets_data.json()['bouquets']
        for b in bouquets:
            if list_bouquets:
                print("Found bouquet: {}".format(b[1]))
            if b[1] == bouquet or not bouquet:
                result[b[1]] = b[0]
    except Exception:
        raise
    return result


def getBouquetsServices(bouquets, api_root_url):
    services = {}
    try:
        for bouquet_name, bouquet_svc_ref in bouquets.items():
            url = '{}/api/getservices?sRef={}'.format(api_root_url, bouquet_svc_ref)
            services_data = requests.get(url)
            services[bouquet_name] = services_data.json()['services']
    except Exception:
        raise
    return services


def getEPGs(bouquets_services, api_root_url):
    epg = {}
    for _, services in bouquets_services.items():
        for service in services:
            if service['pos']:
                url = '{}/api/epgservice?sRef={}'.format(api_root_url, service['servicereference'])
                print("{} ({}) ==> {}".format(service['servicename'], service['program'], url))
                try:
                    service_epg_data = requests.get(url)
                    epg[service['program']] = service_epg_data.json()['events']
                except Exception:
                    raise
    return epg


def addChannels2XML(xmltv, bouquets_services, epg, api_root_url):
    for _, services in bouquets_services.items():
        for service in services:
            if service['pos']:
                channel = etree.SubElement(xmltv, 'channel')
                channel.attrib['id'] = '{}'.format(service['program'])
                etree.SubElement(channel, 'display-name').text = html.unescape(service['servicename'])
                etree.SubElement(channel, 'display-name').text = str(service['pos'])
                if epg[service['program']]:
                    first_event = epg[service['program']][0]
                    channel_picon = etree.SubElement(channel, 'icon')
                    channel_picon.attrib['src'] = '{}{}'.format(api_root_url, first_event['picon'])
    return xmltv


# def addCategories2Programme_(programme, event):
#     sd = event['shortdesc']
#     programme_category = etree.SubElement(programme, 'category')
#     programme_category.attrib['lang'] = 'en'
#     if sd != '':
#         categories = sd[sd.find('[')+1:sd.find(']')].split('. ')
#         if len(categories) > 0:
#             programme_category.text = categories[0]
#         else:
#             programme_category.text = 'Show'    
#         if len(categories) > 1:
#             programme_keyword = etree.SubElement(programme, 'keyword')
#             programme_keyword.text = html.unescape(categories[1])
#             programme_keyword.attrib['lang'] = 'en'
#     else:
#         programme_category.text = 'Show'
#     return programme


def addCategories2Programme(programme, event):
    programme_category = etree.SubElement(programme, 'category')
    programme_category.attrib['lang'] = 'en'
    category = re.search(r'^\[([\w\s]+)\]', event['shortdesc'])
    if category:
        programme_category.text = '{}'.format(category.group(1))
    else:
        programme_category.text = 'Show'
    return programme


def addSeriesInfo2Programme(programme, event):
    epnum = re.search(r'[SE]+[\dE]+[\d]*', event['shortdesc'])
    original_air_date = re.search( r'(\d\d)/(\d\d)/(\d\d\d\d)', event['shortdesc'])
    if epnum:
        epnum = epnum.group()
        programme_epnum = etree.SubElement(programme, 'episode-num')
        programme_epnum.attrib['system'] = 'xmltv_ns'
        series_num = re.search(r'S([\d]+)', epnum)
        episode_num = re.search(r'E([\d]+)', epnum)
        if series_num:
            series_num = int(series_num.group(1)) - 1
        else:
            series_num = ''
        if episode_num:
            episode_num = int(episode_num.group(1)) - 1
        else:
            episode_num = ''
        programme_epnum.text = '{}.{}.'.format(series_num, episode_num)
    elif original_air_date:
        programme_epnum = etree.SubElement(programme, 'episode-num')
        programme_epnum.attrib['system'] = 'original-air-date'
        programme_epnum.text = "{}-{}-{}".format(
            original_air_date.group(3),
            original_air_date.group(2),
            original_air_date.group(1))
    else:
        original_air_date = re.search( r'(\d\d).(\d\d).(\d\d\d\d)', event['date'])
        programme_epnum = etree.SubElement(programme, 'episode-num')
        programme_epnum.attrib['system'] = 'original-air-date'
        programme_epnum.text = "{}-{}-{}".format(
            original_air_date.group(3),
            original_air_date.group(2),
            original_air_date.group(1))

    return programme


def addEvents2XML(xmltv, epg):
    for service_program, events in epg.items():
        for event in events:
            # Time Calculations and transformations
            start_dt = datetime.fromtimestamp(event['begin_timestamp'])
            start_dt_str = start_dt.strftime("%Y%m%d%H%M%S")
            end_dt = start_dt + timedelta(minutes=event['duration'])
            end_dt_str = end_dt.strftime("%Y%m%d%H%M%S")

            programme = etree.SubElement(xmltv, 'programme')
            programme.attrib['channel'] = str(service_program)
            programme.attrib['start'] = start_dt_str
            programme.attrib['stop'] = end_dt_str

            programme_desc = etree.SubElement(programme, 'desc')
            programme_desc.text = html.unescape(event['longdesc'])
            programme_desc.attrib['lang'] = 'en'

            programme_title = etree.SubElement(programme, 'title')
            programme_title.text = html.unescape(event['title'])
            programme_title.attrib['lang'] = 'en'

            
            subtitle_first_step = re.sub(r'^(\[.+\]\s*)', '', event['shortdesc'])
            subtitle = re.sub(r'\s*\([SE]\d+.*\)', '', subtitle_first_step)
            if len(subtitle) > 0:
                programme_subtitle = etree.SubElement(programme, 'sub-title')
                programme_subtitle.text = html.unescape(subtitle)
                programme_subtitle.attrib['lang'] = 'en'

            programme = addCategories2Programme(programme, event)
            programme_type = programme.find('category').text
            if programme_type in ['Series', 'Show']:
                programme = addSeriesInfo2Programme(programme, event)
            

    return xmltv


def generateXMLTV(bouquets_services, epg, api_root_url):
    xmltv = etree.Element('tv')
    xmltv.attrib['generator-info-url'] = 'https://github.com/cvarelaruiz'
    xmltv.attrib['generator-info-name'] = 'OpenWebIf 2 Plex XMLTV'

    xmltv = addChannels2XML(xmltv, bouquets_services, epg, api_root_url)
    xmltv = addEvents2XML(xmltv, epg)

    return etree.tostring(xmltv, pretty_print=True)


@click.command()
@click.option('-b', '--bouquet', help='The name of the bouquet to parse. If not'
              ' specified parse all bouquets.', type=click.STRING)
@click.option('-u', '--username', help='OpenWebIf Username', type=click.STRING)
@click.option('-p', '--password', help='OpenWebIf Password', type=click.STRING)
@click.option('-h', '--host', help='OpenWebIf Host', default='localhost',
    type=click.STRING)
@click.option('-P', '--port', help='OpenWebIf Port', default=80, type=click.INT)
@click.option('-o', '--output-file', help='Output file', default='epg.xml',
    type=click.STRING)
@click.option('-l', '--list-bouquets', help='Display a list of bouquets.', 
    is_flag=True)
def main(bouquet=None, username=None, password=None, host='localhost', port=80,
    output_file='epg.xmltv', list_bouquets=False):
    api_root_url = getAPIRoot(username=username, password=password, host=host, port=port)
    bouquets = getBouquets(bouquet=bouquet, api_root_url=api_root_url,
        list_bouquets=list_bouquets)
    bouquets_services = getBouquetsServices(bouquets=bouquets, api_root_url=api_root_url)
    epg = getEPGs(bouquets_services=bouquets_services, api_root_url=api_root_url)
    xmltv = generateXMLTV(bouquets_services, epg, api_root_url)
    with open(output_file, 'w') as xmltv_file:
        xmltv_file.write(xmltv.decode("utf-8"))


if __name__ == '__main__':
    main()