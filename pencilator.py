#! python3
# This is a script to visit the Zen Pencils website, 
# which is one of my favourite comic book sites, and compile all comics into one PDF

#Import the necessary libraries
import requests, os, bs4, time, re, math
import numpy as np
from PIL import Image
from fpdf import FPDF
from os import listdir
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PyPDF2 import PdfFileMerger, PdfFileReader

# Variable names
zenPencilLink = "https://zenpencils.com/comic/1-ralph-waldo-emerson-make-them-cry/"
path = "./zenPencils/"
pdfPath = './zenPDFs/'
os.makedirs(path, exist_ok=True)     # Folder for images
os.makedirs(pdfPath, exist_ok=True)  # Folder for PDFs
comicCount = 0    # Keeps track of number of comics
count = 1         # Keeps track of image names
pageSize = 1450   # Found to work best by empirical methods
threshold = 0.97  # Found to work best by empirical methods
tempFilePath = './zenPencils/temp.gif'

# Request with backoff hits the url repeatedly with a higher timeout between requests if the site throws a connection error due to repeated requests
def requestWithBackOff(url):
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session.get(url)

# To return integer version of string
def tryint(s):
    try:
        return int(s)
    except:
        return s

# To split a file into fileName, number and extension
def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

# To sort functions first by fileName, next by number and next by extension by key
def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)

# Iterates through a list of images and appends them to create a PDF
def pdfCreate(fileName, path, imageList):
    pdf = FPDF('P','mm','A4') # create an A4-size pdf document 
    x,y,w = 0,0,200
    for image in imageList:
        print("Image "+ image)
        pdf.add_page()
        pdf.image(path + image,x,y,w)
    pdf.output(fileName,"F")
    print("Done")

# Hits a URL and saves the content into a file
def downloadContent(fileName, URL):
    res = requestWithBackOff(URL)
    downloadFile = open(fileName, 'wb')
    for chunk in res.iter_content(100000):
        downloadFile.write(chunk)
    downloadFile.close()

# Finds the gutters of the comic and crops them into pages of suitable size
def cropImage(im, pageSize, threshold, path, count):
    maxHeight = pageSize
    colSize = im.size[0]
    rowSize = im.size[1]
    array_ = np.array(im)

    # Margins stores the y coordinates of the gutters
    # Rowsums computes the sum of pixels in every row. Gutters will have a higher value because they are white
    margins = [0]
    flag = True
    rowSums = np.sum(array_, axis=1)
    if len(np.shape(rowSums)) > 1:          # For RGB images
        rowSums = np.sum(rowSums, axis=1)
    maxValue = max(rowSums)                # The value of rowSum for a gutter
    minimumHeight = 100                    # Discard frames without pictures

    # Checks for the places where whitespace changes into color. The values of y coordinates of margins
    for x in range(rowSize):
        if flag == True and rowSums[x] < math.floor(threshold * maxValue):
                margins.append(x)
                flag = False
        if flag == False and rowSums[x] > math.floor(threshold * maxValue):
                margins.append(x)
                flag = True

    cropPoints = []

    # Determines the points where cropping will occur based on page length and width of margin
    for i in range(0, len(margins), 2):
        if i+1 < len(margins) and margins[i] <= maxHeight and margins[i+1] > maxHeight:
            cropPoints.append(math.floor((margins[i] + margins[i+1])/2))
            maxHeight = math.floor((margins[i] + margins[i+1])/2) + pageSize
        elif margins[i] > maxHeight:
            cropPoints.append(math.floor((margins[i-1] + margins[i-2])/2))
            maxHeight = math.floor((margins[i-1] + margins[i-2])/2) + pageSize
    cropPoints.append(rowSize)

    # Iterate through the image and crop the image
    xTop, yTop = 0, 0
    for cropPoint in cropPoints:
        if yTop == rowSize:
            break
        region = im.crop((xTop, yTop, colSize, cropPoint))
        if region.size[1] > minimumHeight:
            region.save(path + str(count) + '.' + im.format.lower(), im.format)
            count += 1
        yTop = cropPoint   

    return count

# Runs through a folder and merges all PDFs in the folder
def mergePDF(fileName, folderPath):
    merger = PdfFileMerger()
    pdfList = os.listdir(folderPath)
    newList = []
    for pdf in pdfList:
        if pdf.endswith('.pdf'):
         newList.append(pdf)

    sort_nicely(newList)

    for pdf in newList:
        merger.append(PdfFileReader(open(pdf, 'rb')))

    merger.write(fileName)

# Removes a directory recursively
def removeDirectory(pathName):
    for file in os.listdir(pathName):
        print("Removing file "+ file)
        os.remove(pathName + file)
    os.removedirs(pathName)

# Main flow starts

while True:
    # Obtain content from site
    comicCount += 1
    print("Downloading comic "+ str(comicCount))
    res = requestWithBackOff(zenPencilLink)
    res.raise_for_status()

    # Select all image tags and save URLs
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    imageTag = soup.select('#comic img')
    imageURLlist = []
    for tag in imageTag:
        imageURL = tag.get('src')
        imageURLlist.append(imageURL)

    # Download images and rename or crop them and save
    for imageURL in imageURLlist:
        downloadContent(tempFilePath, imageURL)
        im = Image.open(tempFilePath)
        if im.size[1] < pageSize:
            os.rename(tempFilePath, path + str(count) + '.' + im.format.lower())
            count += 1
        else:
            count = cropImage(im, pageSize, threshold, path, count)
            os.remove(tempFilePath)
        im.close()

    # Check for the URL for the next comic and exit if it doesn't exist
    zenPencilTag = soup.select('.comic_navi_right a')
    if len(zenPencilTag) == 0:
        break
    zenPencilLink = zenPencilTag[0].get('href')

# Iteratively create PDFs of 100 images at a time (because too many images cannot be appended or FPDF fails)
imageList = os.listdir(path)
newList = []
for image in imageList:
    if image.endswith('.gif') or image.endswith('.jpeg') or image.endswith('.png'):
        newList.append(image)
sort_nicely(newList)
for i in range(10):
    pdfCreate(pdfPath + str(i) + "zenComics.pdf", path, newList[i*100:(i+1)*100])
i = i+1
pdfCreate(pdfPath + str(i) + "zenComics.pdf", path, newList[1000:])

# Merge all created PDFs
mergePDF("zenComics.pdf", pdfPath)

# Remove the directories which contain images and PDFs
removeDirectory(pdfPath)
removeDirectory(path)
 