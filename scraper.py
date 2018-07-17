# -*- coding: utf-8 -*-

#### IMPORTS 1.0

import os
import re
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup


#### FUNCTIONS 1.0

def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9QY][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9QY][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    now = datetime.now()
    year, month = date[:4], date[5:7]
    validYear = (2000 <= int(year) <= now.year)
    if 'Q' in date:
        validMonth = (month in ['Q0', 'Q1', 'Q2', 'Q3', 'Q4'])
    elif 'Y' in date:
        validMonth = (month in ['Y1'])
    else:
        try:
            validMonth = datetime.strptime(date, "%Y_%m") < now
        except:
            return False
    if all([validName, validYear, validMonth]):
        return True


def validateURL(url):
    try:
        r = urllib2.urlopen(url)
        count = 1
        while r.getcode() == 500 and count < 4:
            print ("Attempt {0} - Status code: {1}. Retrying.".format(count, r.status_code))
            count += 1
            r = urllib2.urlopen(url)
        sourceFilename = r.headers.get('Content-Disposition')

        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        else:
            ext = os.path.splitext(url)[1]
        validURL = r.getcode() == 200
        validFiletype = ext.lower() in ['.csv', '.xls', '.xlsx', '.pdf']
        return validURL, validFiletype
    except:
        print ("Error validating URL.")
        return False, False


def validate(filename, file_url):
    validFilename = validateFilename(filename)
    validURL, validFiletype = validateURL(file_url)
    if not validFilename:
        print filename, "*Error: Invalid filename*"
        print file_url
        return False
    if not validURL:
        print filename, "*Error: Invalid URL*"
        print file_url
        return False
    if not validFiletype:
        print filename, "*Error: Invalid filetype*"
        print file_url
        return False
    return True


def convert_mth_strings ( mth_string ):
    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    for k, v in month_numbers.items():
        mth_string = mth_string.replace(k, v)
    return mth_string


#### VARIABLES 1.0

entity_id = "E3833_CDC_gov"
url = "http://www.chichester.gov.uk/paymentsover500pounds"
errors = 0
data = []


#### READ HTML 1.0

html = urllib2.urlopen(url)
soup = BeautifulSoup(html, 'lxml')

#### SCRAPE DATA

year_links = soup.find('ul', attrs = {'class': 'list-unstyled tasks-top'}).find_all('a')
for year_link in year_links:
    if 'http' not in year_link['href']:
        year_url = 'http://www.chichester.gov.uk'+year_link['href']
    else:
        year_url = year_link['href']
    year_html = urllib2.urlopen(year_url)
    year_soup = BeautifulSoup(year_html, 'lxml')
    try:
        blocks = year_soup.find('ul', 'list-group').find_all('a')
    except:
        blocks = year_soup.find('ul', 'list-unstyled itemcount2').find_all('a')
    for block in blocks:
        url = block['href']
        if 'http' not in url:
            url = 'http://www.chichester.gov.uk'+url
        else:
            url = url
        file_name = block.text
        if ('csv' in file_name or 'excel' in file_name) and '2010' not in year_url:
            if ('October' in file_name and 'December' in file_name) or ('Oct' in file_name and 'Dec' in file_name):
                csvMth = 'Q4'
                match = re.search(r'.*([1-3][0-9]{3})', file_name)
                if match is not None:
                    csvYr = match.group(1)
            elif ('July' in file_name and 'September' in file_name) or ('July' in file_name and 'Sept' in file_name) or ('Jul' in file_name and 'Sep' in file_name):
                csvMth = 'Q3'
                match = re.search(r'.*([1-3][0-9]{3})', file_name)
                if match is not None:
                    csvYr = match.group(1)
            elif ('April' in file_name and 'June' in file_name) or ('Apr' in file_name and 'Jun' in file_name):
                csvMth = 'Q2'
                match = re.search(r'.*([1-3][0-9]{3})', file_name)
                if match is not None:
                    csvYr = match.group(1)
            elif 'January' in file_name and 'March' in file_name:
                csvMth = 'Q1'
                match = re.search(r'.*([1-3][0-9]{3})', file_name)
                if match is not None:
                    csvYr = match.group(1)
            elif 'Full Year' in file_name:
                csvMth = 'Y1'
                match = re.search(r'.*([1-3][0-9]{3})', file_name)
                if match is not None:
                    csvYr = match.group(1)
            else:
                csvMth = file_name[:3]
                csvYr = file_name.split()[1]
            csvMth = convert_mth_strings(csvMth.upper())
            data.append([csvYr, csvMth, url])

    if '2010' in year_url:
        blocks = year_soup.find('ul', 'list-group').find_all('li')[1:]
        for block in blocks:
            pdf_link = block.find('a')['class'][-1]
            if 'pdf' in pdf_link:
                csv_file_name = block.find_next('li').find('a')
                try:
                    url = block.find_next('li').find('a')['href']
                except:
                    break
                if csv_file_name:
                    csv_file_name = csv_file_name.text
                    csvMth = csv_file_name[:3]
                    csvYr = csv_file_name.split()[1]
                    csvMth = convert_mth_strings(csvMth.upper())
                    data.append([csvYr, csvMth, url])


#### STORE DATA 1.0

for row in data:
    csvYr, csvMth, url = row
    filename = entity_id + "_" + csvYr + "_" + csvMth
    todays_date = str(datetime.now())
    file_url = url.strip()

    valid = validate(filename, file_url)

    if valid == True:
        scraperwiki.sqlite.save(unique_keys=['l'], data={"l": file_url, "f": filename, "d": todays_date })
        print filename
    else:
        errors += 1

if errors > 0:
    raise Exception("%d errors occurred during scrape." % errors)


#### EOF
