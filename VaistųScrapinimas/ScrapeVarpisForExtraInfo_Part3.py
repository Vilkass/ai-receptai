from playwright.async_api import async_playwright
import asyncio
import os
import pandas as pd
import re
import string
import time

savePath = "urpath/"
def ReadExcelFile():
    filename = savePath+"VaistaiSuInfo.xlsx"
    if os.path.exists(filename):
        df = pd.read_excel(filename)
        return df
    else:
        print("File does not exist.")
        return pd.DataFrame()  # Return an empty DataFrame if the file does not exist
    
def update_excel_file(data):
    filename = savePath+"VaistaiSuInfoFinal.xlsx"
    
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

async def CollectInfo(page):
    veikliojiMedziaga = page.locator("#content > div > div.row.mt30 > div.col-md-8 > div > div:nth-child(2) > div > p")
    veikliojiMedziagaText = await veikliojiMedziaga.inner_text()
    vartojimoBudas = page.locator("#content > div > div.row.mt30 > div.col-md-8 > div > div:nth-child(5) > div > p")
    vartojimoBudasText = await vartojimoBudas.inner_text()
    print(vartojimoBudasText)
    return veikliojiMedziagaText, vartojimoBudasText
async def RunBrowser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await StartUp(browser)
        df=ReadExcelFile()
        for index, row in df.iterrows():
            page= await  GoToSite(row["vaprisHref"],context)
            row["veikliojiMedziagaText"],row["vartojimoBudas"] = await CollectInfo(page)
            update_excel_file(row)


        
if __name__ == "__main__":
    asyncio.run(RunBrowser())