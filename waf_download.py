#!/usr/bin/env python

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download and print metadata of ISO documents from ERDDAP instance')
    parser.add_argument('destination', help='Folder to download the ISO documents into')
    parser.add_argument('-e', '--erddap', help='URL to ERDDAP, example: https://erddap.icos-cp.eu/erddap/metadata/iso19115/xml/', required=True)
    args = parser.parse_args()

    main(args)
