import json
import re
import sys
import csv
from urllib.parse import quote
from urllib.request import Request, urlopen
import pandas as pd
from bs4 import BeautifulSoup
from newspaper import Article

le_fig_comments = []
csv_list = []
if(sys.argv[1].__contains__(' ')):
    query = sys.argv[1].replace(" ","+")
else:
    query = sys.argv[1]

query_url = "https://www.lemonde.fr/recherche/?keywords=" + query + "&operator=and&exclude_keywords=&qt=recherche_texte_titre&author=&period=custom_date&start_day=" + sys.argv[2].split('-')[0] + "&start_month=" + sys.argv[2].split('-')[1] + "&start_year=" + sys.argv[2].split('-')[2] + "&end_day=" + sys.argv[3].split('-')[0] + "&end_month=" + sys.argv[3].split('-')[1] + "&end_year=" + sys.argv[3].split('-')[2] + "&sort=desc&page_num="
csv_cnt = 0
line_cnt = 0
csvFile = open('le_monde ' + sys.argv[1] + ' from ' + sys.argv[2] + ' to ' + sys.argv[3] + ' part' + str(csv_cnt) + '.csv','w',newline='', encoding="utf-8-sig")
writercsv = csv.writer(csvFile,dialect="excel")
writercsv.writerow(["Comment Id", "Comment Text", "Comment Timestamp", "User Name", "Article Url", "Article Title"])
csv_list.append(writercsv)

def article_title(url):
    remaining_download_tries = 10
    while remaining_download_tries > 0 :
        try:
            a = Article(url,language='fr')
            a.download()
            a.parse()
            return a.title
        except:
            remaining_download_tries = remaining_download_tries - 1
            continue
    return ""

def retry(url, cnt):
    remaining_download_tries = 10
    while remaining_download_tries > 0 :
        try:
            page_content = urlopen(url + str(cnt)).read()
            return page_content
        except:
            remaining_download_tries = remaining_download_tries - 1
            continue
    return "next"

def comment_extraction():
    print("Extracting Comments...")
    global csvFile
    global line_cnt
    global csv_cnt
    comment_links = open(sys.argv[1] + '_urls.txt', 'r')
    for link in comment_links:
        i = 2
        page_content = retry(link, "")
        if(page_content == "next" or page_content == None):
            continue
        else:
            page_content.decode("utf-8")
        comment_cauldron = BeautifulSoup(page_content, 'html.parser')
        for com in comment_cauldron.find_all(attrs={"itemprop": "commentText"}):
            comment_text = com.find(lambda tag: tag.name == 'p' and not tag.attrs).getText() + "\n"
            comment_id = com.attrs["data-reaction_id"]
            comment_date = com.find("p", attrs={"class": "references"}).contents[1].getText()
            user_name = com.find("p", attrs={"class": "references"}).contents[0]
            line_cnt += 1
            csv_list[csv_cnt].writerow([comment_id, comment_text, comment_date.replace(" - ", " "), user_name, link.replace("/reations/", "/article/"), article_title(link.replace("/reations/", "/article/"))])
            if(line_cnt > 100000):
                csvFile.close()
                csv_cnt += 1
                csvFile = open(sys.argv[1] + ' from ' + sys.argv[2] + ' to ' + sys.argv[3] + ' part' + str(csv_cnt) + '.csv','w',newline='', encoding="utf-8-sig")
                writercsv = csv.writer(csvFile,dialect="excel")
                csv_list.append(writercsv)
                line_cnt = 0
        if(not comment_cauldron.find(attrs={"class": "next obf"})):
            continue
        while(1):
            page_content = retry(link.replace(".html","_" + str(i) + ".html"), "")
            if(page_content == "next" or page_content == None):
                continue
            else:
                page_content.decode("utf-8")
            comment_cauldron = BeautifulSoup(page_content, 'html.parser')
            for com in comment_cauldron.find_all(attrs={"itemprop": "commentText"}):
                comment_text = com.find(lambda tag: tag.name == 'p' and not tag.attrs).getText() + "\n"
                comment_id = com.attrs["data-reaction_id"]
                comment_date = com.find("p", attrs={"class": "references"}).contents[1].getText()
                user_name = com.find("p", attrs={"class": "references"}).contents[0]
                line_cnt += 1
                csv_list[csv_cnt].writerow([comment_id, comment_text, comment_date.replace(" - ", " "), user_name, link.replace("/reations/", "/article/"), link.replace("/reations/", "/article/")])
            if(line_cnt > 100000):
                csvFile.close()
                csv_cnt += 1
                csvFile = open('le_monde ' + sys.argv[1] + ' from ' + sys.argv[2] + ' to ' + sys.argv[3] + ' part' + str(csv_cnt) + '.csv','w',newline='', encoding="utf-8-sig")
                writercsv = csv.writer(csvFile,dialect="excel")
                csv_list.append(writercsv)
                line_cnt = 0
            i += 1
            if(not comment_cauldron.find(attrs={"class": "next obf"})):
                break

def query_extration(url):
    print("\nSearching Articles...")
    query_html = open("query_html" + query + ".txt", "w")
    query_urls = open(sys.argv[1] + '_urls.txt','w')
    le_fig_articles = {}
    i = 1
    page_content = retry(url, i).decode("utf-8")
    query_soup = BeautifulSoup(page_content,'html.parser')
    query_html.write(str(query_soup.prettify().encode("utf-8")))
    max_it = int(query_soup.find("li", class_="adroite").find("a").getText())
    i+=1
    while(i <= max_it):
        page_content = retry(url, i)
        if(page_content == "next" or page_content == None):
            continue
        else:
            page_content.decode("utf-8")
        query_soup = BeautifulSoup(page_content,'html.parser')
        query_html.write(str(query_soup.prettify().encode("utf-8")))
        i = i+1
    query_html.close()
    query_html = open("query_html" + query + ".txt", 'r').read()
    query_cauldron = BeautifulSoup(query_html,'html.parser')
    for com in query_cauldron.find_all("a", class_="grid_3 alpha obf"):
        query_urls.write("https://www.lemonde.fr" + com.get("href").split("?")[0].replace("/article/", "/reactions/") + "\n")
    query_urls.close()

query_extration(query_url)
comment_extraction()

csvFile.close()