#! python3
#This script hits the link for the 2048 game and continuously hitting up, right, down, left till Game is over

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

browser = webdriver.Firefox()
browser.get('https://gabrielecirulli.github.io/2048/')
htmlElem = browser.find_element_by_tag_name('html')
flag = False
while True:
    try:
        retry = browser.find_element_by_class_name('game-over')
        print('<%s>'% (retry.tag_name))
        for letter in retry.tag_name:
		        if letter == 'v':
			          flag=True
			          break
        if flag == True:
            break
    except:
        print('Sending keys...')
        htmlElem.send_keys(Keys.UP)     # scrolls to bottom
        htmlElem.send_keys(Keys.RIGHT)    # scrolls to top
        htmlElem.send_keys(Keys.DOWN)
        htmlElem.send_keys(Keys.LEFT)
