#!/usr/bin/env python3
import click
import requests

from lxml import etree
from datetime import datetime, timedelta


def getAPIRoot(username, password, host, port):
    if username:
        url = 'http://{}:{}@{}:{}/api'.format(
                username, password, host, port)
    else:
        url = 'http://{}:{}/api'.format(host, port)
    return url


def getBouquets(bouquet, api_root_url):
    """
    Function to get the list of bouquets
    """
    result = {}
    url = '{}/bouquets'.format(api_root_url)
    try:
        bouquets_data = requests.get(url)
        bouquets = bouquets_data.json()['bouquets']
        for b in bouquets:
            if b[1] == bouquet or not bouquet:
                result[b[1]] = b[0]
    except Exception:
        raise
    return result


def getServices(bouquets, api_root_url):
    services = {}
    try:
        for bouquet_name, bouquet_svc_ref in bouquets.items():
            url = '{}/getservices?sRef={}'.format(api_root_url, bouquet_svc_ref)
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
                url = '{}/epgservice?sRef={}'.format(api_root_url, service['servicereference'])
                print("{} ==> {}".format(service['program'], url))
                try:
                    service_epg_data = requests.get(url)
                    epg[service['program']] = service_epg_data.json()['events']
                except Exception:
                    raise
    return epg


def generateXMLTV(bouquets_services, epg):
    xmltv = etree.Element('tv')
    xmltv.attrib['generator-info-url'] = 'https://github.com/cvarelaruiz'
    xmltv.attrib['generator-info-name'] = 'OpenWebIf 2 Plex XMLTV'
    for _, services in bouquets_services.items():
        for service in services:
            if service['pos']:
                channel = etree.SubElement(xmltv, 'channel')
                channel.attrib['id'] = '{}'.format(service['program'])
                etree.SubElement(channel, 'display-name').text = service['servicename']
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
            programme_desc.text = event['longdesc']
            programme_desc.attrib['lang'] = 'en'

            programme_title = etree.SubElement(programme, 'title')
            programme_title.text = event['title']
            programme_title.attrib['lang'] = 'en'

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
def main(bouquet=None, username=None, password=None, host='localhost', port=80,
    output_file='epg.xmltv'):
    api_root_url = getAPIRoot(username=username, password=password, host=host, port=port)
    bouquets = getBouquets(bouquet=bouquet, api_root_url=api_root_url)
    bouquets_services = getServices(bouquets=bouquets, api_root_url=api_root_url)
    epg = getEPGs(bouquets_services=bouquets_services, api_root_url=api_root_url)
    xmltv = generateXMLTV(bouquets_services, epg)
    with open(output_file, 'w') as xmltv_file:
        xmltv_file.write(xmltv.decode("utf-8"))


if __name__ == '__main__':
    main()