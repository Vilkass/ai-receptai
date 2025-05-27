from playwright.async_api import async_playwright
import asyncio
import os
import pandas as pd
import re
import string
import time

url = "https://vapris.vvkt.lt/vvkt-web/public/medications"
savePath = "urpath/"
async def StartUp(browser):
    context = await browser.new_context()
    return context

async def GoToSite(url,context):
    if context.pages:
        page = context.pages[0]
    else:
        page = await context.new_page()
    await page.goto(url)
    return page

def update_excel_file(data):
    filename = savePath+"VaistaiSuInfo.xlsx"
    
    # Ensure directory exists

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Convert to DataFrame if needed
    #print(data)
    df = pd.DataFrame([data])


    # Load existing data if file exists
    if os.path.exists(filename):
        existing_df = pd.read_excel(filename)
        df = pd.concat([existing_df, df], ignore_index=True)

    # Save the DataFrame to Excel
    df.to_excel(filename, index=False, engine='openpyxl')

async def TypeIntoSearchBar(page, search_text,case):
    if case==0:
        input_selector = "#medPublicSearch > div > div > div.col-md-6.col-md-offset-3 > div > input"
        await page.fill(input_selector, search_text)
        click_enter = "#medPublicSearch > div > div > div.col-md-6.col-md-offset-3 > div > span > button"
    else:
        input_selector = "#medPublicSearch > div.search-bg > div > div > div.col-md-8 > div > input"
        await page.fill(input_selector, search_text)
        click_enter = "#medPublicSearch > div.search-bg > div > div > div.col-md-8 > div > span > button "
    ##medPublicSearch > div > div > div.col-md-6.col-md-offset-3 > div > span > button
    ##medPublicSearch > div.search-bg > div > div > div.col-md-8 > div > input
    await page.click(click_enter)
    return page

def ReadExcelFile():
    filename = savePath+"EurovaistineVaistai.xlsx"
    if os.path.exists(filename):
        df = pd.read_excel(filename)
        return df
    else:
        print("File does not exist.")
        return pd.DataFrame()  # Return an empty DataFrame if the file does not exist

async def PatikrintiOpcijas(page,dosage,forma):
    vaistai=await page.query_selector_all("#content > div > div > div:nth-child(1) > div")
    print("Found options:"+ str(len(vaistai)))
    for vaistas in vaistai:
        medDosage=await vaistas.query_selector("css= ul > li > span.meta > span:nth-child(5)")
        #content > div > div > div:nth-child(1) > div:nth-child(1) > ul > li > span.meta
        medForma=await vaistas.query_selector("css= ul > li > span.meta > span:nth-child(8)")
        ##content > div > div > div:nth-child(1) > div:nth-child(1) > ul > li > span.meta > span:nth-child(8)
        medDosage=await medDosage.inner_text()
        medForma=await medForma.inner_text()
        medDosage=medDosage.strip()
        medForma=medForma.strip()
        #print(medDosage)
        #print("Dosage: "+dosage)
        #print(medDosage==dosage)
        #print(medForma)
        #print("Forma: "+forma)
        #print(medForma==forma)        
        if medDosage==dosage and medForma==forma:
            
            vaistoHref=await vaistas.query_selector("css= ul > li > a")
            ##content > div > div > div:nth-child(1) > div:nth-child(2) > ul > li > a
            print("vaistas: "+await vaistoHref.inner_text())
            vaistoHref=await vaistoHref.get_attribute("href")
            return vaistoHref
        return None
async def RunBrowser(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await StartUp(browser)
        page= await  GoToSite(url,context)
        df=ReadExcelFile()
        varpisHref="https://vapris.vvkt.lt"
        for index, row in df.iterrows():
            search_text = row['name']
            print(f"Name : {search_text}, Dosage: {row['dosage']}, Forma: {row['definition']}")
            page=await TypeIntoSearchBar(page, search_text,index)
            vaistoVaprisHref=await PatikrintiOpcijas(page,row['dosage'],row['definition'])
            if vaistoVaprisHref:
                print("Vaisto href: " + str(vaistoVaprisHref))
                row['vaprisHref'] = varpisHref+vaistoVaprisHref
                update_excel_file(row)
                #time.sleep(200)
        
if __name__ == "__main__":
    asyncio.run(RunBrowser(url))
