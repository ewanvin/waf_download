#!/usr/bin/env python
'''
scripts/waf_download.py

A script to scrape ISO 19115 Documents from a running ERDDAP instance. In the
case of Glider DAC, this should download from the public ERDDAP instance. The
documents should be in a directory with no other contents and served as a
static directory.
'''

import requests
import argparse
import os
import re
from html.parser import HTMLParser
from xml.etree import ElementTree

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.xml_files = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href and href.endswith('.xml'):
                self.xml_files.append(href)

def main(args):
    check_destination(args.destination)
    if args.erddap:
        get_erddap_metadata(args.erddap, args.destination)

def get_erddap_metadata(url, destination):
    '''
    Scrapes the available datasets from ERDDAP, downloads the .xml files,
    and prints the metadata of the ISO 19115 documents that are available.
    '''
    url = url.rstrip('/')
    response = requests.get(url)
    if response.status_code != 200:
        raise IOError(f"Failed to get index from ERDDAP at {url}")

    parser = MyHTMLParser()
    parser.feed(response.text)

    for xml_file in parser.xml_files:
        file_url = os.path.join(url, xml_file)
        file_name = os.path.basename(xml_file)
        download_file(file_url, destination, file_name)
        print(f"Found XML file: {file_url}")
        print_xml_metadata(os.path.join(destination, file_name))

def check_destination(destination_path):
    '''
    Creates the directory if it doesn't exist
    '''
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

def download_file(file_url, destination_path, file_name):
    '''
    Downloads a file from the specified URL to the destination path
    '''
    response = requests.get(file_url, stream=True)
    if response.status_code != 200:
        raise IOError(f"Failed to retrieve file from {file_url} with error code {response.status_code}")

    file_path = os.path.join(destination_path, file_name)
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:
                f.write(chunk)
                f.flush()

    print("Downloaded file to", file_path)

def print_xml_metadata(file_path):
    '''
    Parses and prints metadata of an XML document at the file path specified
    '''
    with open(file_path, 'r') as f:
        xml_content = f.read()
    
    print(f"Metadata for {file_path}:")
    print(xml_content[:500])  # Print the first 500 characters of the XML content for simplicity
    
    # Parse the XML content to find data types
    print_xml_data_types(xml_content)
    # Print all elements
    print_all_elements(xml_content)

def print_xml_data_types(xml_content):
    '''
    Parses the XML content to find and print the types of available data
    '''
    try:
        tree = ElementTree.fromstring(xml_content)
        namespaces = {
            'gmd': 'http://www.isotc211.org/2005/gmd',
            'gmi': 'http://www.isotc211.org/2005/gmi',
            'gco': 'http://www.isotc211.org/2005/gco',
            'xlink': 'http://www.w3.org/1999/xlink',
            # Add other namespaces as needed
        }   
        
        data_types = []
        
        # Extracting data types from specific XML tags
        for elem in tree.findall('.//gmd:contentInfo//gmi:MI_CoverageDescription//gmd:dimension//gmd:MD_Band//gmd:sequenceIdentifier//gco:MemberName//gco:aName//gco:CharacterString', namespaces):
            data_type = elem.text
            if data_type:
                data_types.append(data_type)
        
        if data_types:
            print("Available Data Types:", ", ".join(data_types))
        else:
            print("No data types found.")
    
    except ElementTree.ParseError as e:
        print(f"Failed to parse XML content: {e}")

def print_all_elements(xml_content):
    '''
    Prints all elements and their text content in the XML
    '''
    try:
        tree = ElementTree.fromstring(xml_content)
        for elem in tree.iter():
            print(f"Tag: {elem.tag}, Text: {elem.text}")
    except ElementTree.ParseError as e:
        print(f"Failed to parse XML content: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download and print metadata of ISO documents from ERDDAP instance')
    parser.add_argument('destination', help='Folder to download the ISO documents into')
    parser.add_argument('-e', '--erddap', help='URL to ERDDAP, example: https://erddap.icos-cp.eu/erddap/metadata/iso19115/xml/', required=True)
    args = parser.parse_args()

    main(args)
