import os
from http import server
from turtle import width
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from datetime import datetime
import pandas as pd
import tkinter as tk
from tkinter import LEFT, TOP, X, OptionMenu, Radiobutton, StringVar, filedialog as fd
from tkinter import ttk
from tkinter.messagebox import showinfo


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
        "Company Name Searched":"Company Name Searched",
        "Company Name Result":"Company Name Result",
        "Numéro d'entreprise du Québec (NEQ)": "ID",
        "Nom": "Company name",
        "Nom de famille": "Owner Lastname",
        "Prénom": "Owner Firstname",
        "Adresse": "Address"
}

def getTableData(html):
    soup = BeautifulSoup(html, features="html.parser")
    tableSoup = soup.find("table", {"id": "CPH_K1ZoneContenu1_Cadr_IdSectionResultat_IdSectionResultat_K1DetailsRecherche_K1GrilleDetail"})
    if not tableSoup:
        return [], []
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
    IDS = df[df["Statut"].str.contains("Immatriculée")==True]
    return IDS["Numéro de dossier"].values, IDS["Nom"].values

def getPageHtml(url, searchTerm, wait=0):
    records=[]
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
        IDsOfBusinesses, Names = getTableData(html)        
        print(IDsOfBusinesses)
        for id in range(len(IDsOfBusinesses)):
            page.locator(f'text={IDsOfBusinesses[id]}').first.click()
            time.sleep(wait)
            html = page.content()
            page.locator(
            '#CPH_K1ZoneContenu1_Cadr_Section00_Section00_K1RubanBoutonsRetour_btnBoutonGenerique01').click()
            soup = BeautifulSoup(html, features="html.parser")
            body_soup=soup.find("div", {"id":"CPH_K1ZoneContenu1_Cadr_K1ZoneContenu1_Cadr"})
            record=dict()
            record["Company Name Searched"] = searchTerm
            record["Company Name Result"] = Names[id]
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
    
        browser.close()
        return records
    



root = tk.Tk()
root.title('REQ')
# root.resizable(False, False)
root.geometry('300x150')
root.focus()
csv_file = None
def selected_column(v, dataframe, filename, btn, drop, open_btn):
    btn.pack_forget()
    drop.pack_forget()
    v = list(dict.fromkeys(v))
    url = "https://www.registreentreprises.gouv.qc.ca/RQAnonymeGR/GR/GR03/GR03A2_19A_PIU_RechEnt_PC/PageRechSimple.aspx?T1.CodeService=S00436&Clng=F&WT.co_f=2f96b664f852fde3de71663982802426"
    records = []
    for searchTerm in range(len(v)):
        if v[searchTerm]:	
            records += getPageHtml(url, v[searchTerm], wait=3)            
    if len(records)<1:
        print("No Bussiness records were found for this term")
    df = pd.DataFrame.from_records(records)
    df.rename(columns=column_names, inplace=True)
    df.to_csv(f'Output_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.csv',index=False)
    open_btn.pack( expand=True )
def select_file(csv_file, btn):
    filetypes = (
        ('text files', '*.csv'),
        ('All files', '*.*')
    )

    filename = fd.askopenfilename(
        title='Select a csv',
        initialdir='/',
        filetypes=filetypes)
    if filename:
        showinfo(        
            title='Selected File',
            message=os.path.split(filename)[1]        
        )
    else:
        showinfo(
            title='Error',
            message="File not loaded, Try again"
        )
    csv_file = pd.read_csv(filename)
    # values = dict()
    options = csv_file.keys()
    # for i in range(len(csv_file.keys())):
    #     # print(i, csv_file.keys()[i])
    #     values[csv_file.keys()[i]] = csv_file.keys()[i]

    v = StringVar(root, csv_file.keys()[0])
    
    btn.pack_forget()
    drop = OptionMenu( root , v , *options )
    column_btn = ttk.Button(
        root,
        text='Select this column',
        command=lambda: selected_column(csv_file[v.get()].values, csv_file, filename, column_btn, drop, btn)
    )
    drop.pack(expand=True)
    column_btn.pack(expand=True)
# open button



open_button = ttk.Button(
    root,
    text='Select CSV',
    command=lambda: select_file(csv_file, open_button)
)


# Loop is used to create multiple Radiobuttons
# rather than creating each button separately


open_button.pack(expand=True)
 





# run the application
root.mainloop()



