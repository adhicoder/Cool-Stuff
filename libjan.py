#! python3
# This program is to hit libgen.io and retrieve the first pdf it finds

import requests, os
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fpdf import FPDF

libgenUrl = "http://www.libgen.io/?req="
bookFolder = './libGenBooks/'
os.makedirs(bookFolder, exist_ok=True)     # Folder for books

def requestWithBackOff(url, stream=False):
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session.get(url, stream=stream)

def returnURLList(bookName, format):
    bookList = []
    res = requestWithBackOff(libgenUrl + bookName)
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table', attrs={'class': 'c'})
    rows = table.findAll('tr')
    for row in rows:
        cells = row.findAll('td')
        extension = cells[8].getText()
        if extension == format:
            url = cells[10].find('a').get('href')
            bookList.append(url)
    return bookList

def retrieveLink(url):
    res = requestWithBackOff(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    absoluteURL = url.split(':')[0] + '://' + url.split('/')[2]
    tag1 = soup.select('div .book-info__download')
    tag2 = soup.find()
    if tag1:
        url = tag1[0].find('a').get('href')
    elif tag2:
        table = tag2.find('table')
        cells = table.findAll('td')
        url = cells[2].find('a').get('href')
    else:
        print('No valid URLs')
        return 0
    if url.startswith('/'):
        url = absoluteURL + url
    return url

def downloadContent(fileName, URL):
    res = requestWithBackOff(URL, stream=True)
    downloadFile = open(fileName, 'wb')
    for chunk in res.iter_content(100000):
        downloadFile.write(chunk)
    downloadFile.close()

bookName = input('Enter the name of the book: ')      
bookList = returnURLList(bookName, 'pdf')
url = retrieveLink(bookList[0])
downloadContent(bookFolder + bookName + '.pdf', url) 
