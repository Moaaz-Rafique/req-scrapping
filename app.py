from email import header
from gettext import gettext
import sys
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import csv
import re
import json
import time
from datetime import datetime
import pandas as pd


def deEmojify(text):
    regrex_pattern = re.compile(pattern="["
                                u"\U0001F600-\U0001F64F"  # emoticons
                                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                "]+", flags=re.UNICODE)
    return regrex_pattern.sub(r'', text)

def getTableData(html):
    soup = BeautifulSoup(html, features="html.parser")
    tableSoup = soup.find("table", {"id": "CPH_K1ZoneContenu1_Cadr_IdSectionResultat_IdSectionResultat_K1DetailsRecherche_K1GrilleDetail"})
    header_soup = tableSoup.findAll('th')
    row_soup = tableSoup.findAll('tr')

    # Select header text and turn it into a list for Pandas
    headers = []
    for h in header_soup:
        headers.append(h.text)
    rows = []
    for row in row_soup:
        row_data = []
        for cell in row.findAll('td'):
            row_data.append(cell.text)
        rows.append(row_data)

    # Create the dataframe from your table data
    df = pd.DataFrame(rows, columns=headers)
    # df.to_csv(f'Search_Res_for_{searchTerm}.csv')
    # print(df.info())
    print()
    IDS = df[df["Statut"].str.contains("Immatriculée")==True]["Numéro de dossier"].values
    return IDS

def getPageHtml(url, searchTerm, wait=0):
    with sync_playwright() as p:
        browser = p.webkit.launch(headless=False)  #
        page = browser.new_page()
        # page.evaluate("() => { document.body.style.zoom=0.25; }")
        page.goto(url)
        page.locator(
            '#CPH_K1ZoneContenu1_Cadr_IdSectionRechSimple_IdSectionRechSimple_K1Fieldset1_ChampRecherche__cs').fill(searchTerm)
        page.locator(
            '#CPH_K1ZoneContenu1_Cadr_IdSectionRechSimple_IdSectionRechSimple_CondUtil_CaseConditionsUtilisation_0').check()
        page.locator(
            '#CPH_K1ZoneContenu1_Cadr_IdSectionRechSimple_IdSectionRechSimple_KRBTRechSimple_btnRechercher').click()
        time.sleep(wait)  # uncomment to if network is slow
        html = page.content()        
        IDsOfBusinesses = getTableData(html)
        print(IDsOfBusinesses)
        pages = []
        for i in IDsOfBusinesses:
            page.locator(f'text={i}').first.click()
            time.sleep(wait)
            pages.append(page.content())
            page.locator(
            '#CPH_K1ZoneContenu1_Cadr_Section00_Section00_K1RubanBoutonsRetour_btnBoutonGenerique01').click()
            
    
        # f = open("soup.txt", "a")
        # f.write(pages[-1])
        # f.close()
        browser.close()
        return pages
def findnth(string, substring, n):
    parts = string.split(substring, n + 1)
    if len(parts) <= n + 1:
        return -1
    return len(string) - len(parts[-1]) - len(substring)
    

records = []

url = "https://www.registreentreprises.gouv.qc.ca/RQAnonymeGR/GR/GR03/GR03A2_19A_PIU_RechEnt_PC/PageRechSimple.aspx?T1.CodeService=S00436&Clng=F&WT.co_f=2f96b664f852fde3de71663982802426"
searchTerm = 'valerie simon'



#open and read the file after the appending:
f = open("soup.html", "r")
# print(f.read())

pages = [f.read()]
pages = getPageHtml(url, searchTerm, wait=3)

keys=[
        "Company Name Searched",
        "Company Name Result",
        "Numéro d'entreprise du Québec (NEQ)",
        "Nom",
        "Nom de famille",
        "Prénom",
        "Adresse"
]

column_names = {
    "Numéro d'entreprise du Québec (NEQ)",
        "Nom",
        "Nom de famille",
        "Prénom",
        "Adresse"
}

for page in pages:
    print(len(page))
    soup = BeautifulSoup(page, features="html.parser")
    name_div = soup.findAll("div",{"class": "CPH_K1ZoneContenu1_Cadr_Section01_Section01_ctl04_ctl00_ctl00__cs"})
    body_soup=soup.find("div", {"id":"CPH_K1ZoneContenu1_Cadr_K1ZoneContenu1_Cadr"})
    record=dict()
    # record["Numéro d'entreprise du Québec (NEQ)"] = pages
    for feild in body_soup.findAll("fieldset", {'class': "zonelibellechamp"}):        
        span_soup=feild.findAll("textarea")
        p_soup=feild.findAll("div",{"class": "composantform k1champsaisie validation"})
        if p_soup:
            # print("="*100)
            # print(len(p_soup), len(span_soup))
            for i in range(len(p_soup)):
                # print(p_soup[i].find("span").get_text().strip())
                if p_soup[i].find("span").get_text().strip() in keys:
                    try:
                        record[p_soup[i].find("span").get_text().strip()]=span_soup[i].get_text().strip()
                    except:            
                        (p_soup[i].find("span").get_text().strip(),"-->","undefined")
                elif p_soup[i].find("span").get_text().strip():
                    try:
                        print(p_soup[i].find("span").get_text().strip(),"-->",span_soup[i].get_text().strip())
                        # record[p_soup[i].find("span").get_text().strip()]=span_soup[i].get_text().strip()
                    except:            
                        (p_soup[i].find("span").get_text().strip(),"-->","undefined")

    records.append(record)
# print(records)
# with open(f'Output_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.csv', 'w', encoding="utf-8-sig", errors='surrogatepass', newline='') as output_file:
#     dict_writer = csv.DictWriter(output_file, keys)
#     dict_writer.writeheader()
#     dict_writer.writerows(records)

df = pd.DataFrame.from_records(records, )
df.rename(columns=, inplace=True)
df.to_csv("ot.csv",index=False)