from selenium import webdriver
import re
from bs4 import BeautifulSoup
import time
import json
import os
"""导入库，其中selenium用于模拟浏览器操作，bs4用于解析页面，time库用于计算时间，保证页面的更新时间"""
import pandas as pd

url = 'https://www.renewables.ninja/'
driver = webdriver.Chrome()
driver.get(url)
time.sleep(3)
# point-lat
html = driver.page_source

click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Ok, dismiss this message'))
click_button.click()
time.sleep(3)
click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Login '))
click_button.click()
time.sleep(3)
# driver.find_element_by_id('id_username').clear()
driver.find_element_by_id('id_username').send_keys('1349105084@qq.com')
driver.find_element_by_id('id_password').send_keys('gyh221152')
click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Login'))
click_button.click()

df=pd.read_csv(r'C:\Users\GYHfresh\Desktop\ALLCODE\youhuazu\city.txt')

num=0
for i in df.iloc[:,1].values[64:65]:
    num+=1
    if num%20==0:
        print(num,'超时等待')
        time.sleep(3600)
    print(i)
    driver.find_element_by_id('point-search').clear()
    driver.find_element_by_id('point-search').send_keys(i)
    time.sleep(0.2)
    # soup = BeautifulSoup(html, 'html.parser')
    # print(soup)
    click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Search'))
    click_button.click()
    time.sleep(2)
    click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Solar PV'))
    click_button.click()
    time.sleep(1)
    click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Run'))
    click_button.click()
    time.sleep(8)
    click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Save hourly output as CSV'))
    click_button.click()
    time.sleep(1)

    click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Wind'))
    click_button.click()
    time.sleep(1)
    click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Run'))
    click_button.click()
    time.sleep(8)
    click_button = driver.find_element_by_xpath("//*[text()='{}']".format('Save hourly output as CSV'))
    click_button.click()
    time.sleep(1)