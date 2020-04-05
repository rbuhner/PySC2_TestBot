import requests
import urllib.request
import time
from bs4 import BeautifulSoup

baseurl = 'base url here'
url = 'url goes here'
response = requests.get(url) #Response should be 200 for success
soup = BeautifulSoup(response.text, "html.parser")

soup.findAll('a') #Gets all <a> tags, or hyperlinks; returns as array, accessable via [#]
link = soup.findAll('a')[1]['href'] #Saves partial reference/url link
download_url = baseurl + link
urllib.request.urlretrieve(download_url,'./’'link[link.find('/filename_')+1:])
    #Downloads the first, saves as second; second being a regex of iterative file naming.
time.sleep(1) #To not spam site
