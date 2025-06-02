from playwright.async_api import async_playwright
import asyncio
import os
import pandas as pd
import re
import string
from urllib.parse import urljoin
import time

url = "https://www.eurovaistine.lt/vaistai-nereceptiniai"
savePath = "C:/Users/Daiva/Desktop/Magistro darbas/Dirbtinio intelekto projektų valdymas/docker postgress/VaistųScrapinimas/"
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


async def GetPageCount(page):
    page_count=await page.query_selector("css=div > div > div.paginationWrapper > div.paginationContainer > button:nth-child(6) > span")
    print(await page_count.inner_text())
    return page_count

async def GetPageCount2(page):
    page_count=await page.query_selector("css=div#product-containerPaginator > a.paginator__item.paginator__last")
    ##product-containerPaginator > a.paginator__item.paginator__last
    page_count=await page_count.get_attribute("data-page")
    ###product-containerPaginator > a.paginator__item.paginator__last
    return page_count

async def EuroGetPageItems(page):
    baseURL="https://www.eurovaistine.lt"
    urlList = []
    # Scroll down to load more items
    previous_height = await page.evaluate("document.body.scrollHeight")

    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)  # Wait a bit longer to allow lazy-loaded content

        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

    # Optional: Wait again for any final items to render
    await asyncio.sleep(2)

    # Now select the product items
    items = await page.query_selector_all(".productsListWrapper__cardsContainer > *")

    ##sfreact-reactRenderer68323c287d7034\.32049777 > div > div > div.productsListWrapper > div:nth-child(1)
    print(f"Found {len(items)} items on the page.")
    for item in items:
        try:
            #vaistoText = await item.query_selector("css=div.mainInfo > div.title > span")
            ##\31 9504 > div.content > div.productCardContent > div.mainInfo > div.title > span
            #vaistoKaina = await item.query_selector("css=div.priceContainer > div.productPrice.text-end > span")
            ##\31 9504 > div.content > div.productCardContent > div.priceContainer > div.productPrice.text-end > span
            #dataEntry=await vaistoText.inner_text()
            vaistoURL= await item.query_selector("css= a")
            vaistoURL = await vaistoURL.get_attribute("href")
            ##\33 210
            #print(dataEntry)
            #medicine_info = split_medicine_info(dataEntry)
            #medicine_info["tipas"] = "Nereceptinis vaistas"
            #medicine_info["kaina"] = await vaistoKaina.inner_text()
            #medicine_info["vaistine"] = "Eurovaistine"
            #medicine_info["url"] = baseURL + vaistoURL
            finalUrl=urljoin(baseURL,vaistoURL)
            urlList.append(finalUrl)
            #update_excel_file(medicine_info)
        except Exception as e:
            print(f"Error processing EuroGetPageItems item: {e}")
            continue
    return urlList



def split_medicine_info(line):
    name="empty"
    dosage="empty"
    definition="empty"
    nscore="empty"
    
    try:
        parts = line.split(',')

        nscore = parts[-1]
        definition = parts[-2]
        name = parts[0]
        # Remove last two parts (nscore and definition) from the list
        parts = parts[:-2]
        # Remove the first part (parts[0]) as requested
        if parts:
            parts = parts[1:]
        # Join all parts except last two back with commas — this preserves any commas inside name/dosage

        dosage = ','.join(parts)

        # Add a space between number and measurement in dosage if missing
        dosage = re.sub(r'(\d)([a-zA-ZąčęėįšųūžĄČĘĖĮŠŲŪŽ]+)', r'\1 \2', dosage)

        name=name.strip()
        dosage=dosage.strip()
        definition=definition.strip()
        nscore = nscore.strip()
    except Exception as e:
        print(f"Error parsing line: {line}, Error: {e}")
        
    return {
        "name": name,
        "dosage": dosage,
        "definition": definition,
        "nscore": nscore,
        "full_text": line
    }

def update_excel_file(data):
    filename = savePath+"EurovaistineVaistai.xlsx"
    
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

def ReturnVaistoVartojimas(vaistoInfo):

    vaistoInfo = re.split(r"Kaip vartoti|KAIP VARTOTI", vaistoInfo)
    #print(vaistoInfo)
    if len(vaistoInfo)== 3:
        vaistoInfo = vaistoInfo[2]
        vaistoInfo = re.split(r"Galimas šalutinis poveikis|GALIMAS ŠALUTINIS POVEIKIS", vaistoInfo)
        # Split into lines and remove the first one
        lines = vaistoInfo[0].splitlines()[1:-1]
        # Join the lines back with newline and remove extra newlines
        cleaned = '\n'.join(lines)
        # Replace 2 or more newlines with a single newline
        cleaned = re.sub(r'\n{2,}', '\n', cleaned)
        #print(cleaned)
    return cleaned.strip()


async def EuroReceptiniaiVaistai(page,url,Receptas="Receptinis vaistas"):
    vaistoText = await page.query_selector("css=div.productPage__descriptionBlock > h1")
    ##\33 487 > div:nth-child(1) > div > div:nth-child(2) > div.productPage__descriptionBlock > h1
    vaistoKaina = await page.query_selector("css=div.productPage__priceBlock > div > span")
    ##\33 487 > div:nth-child(1) > div > div:nth-child(2) > div.productPage__priceBlock > div > span
    dataEntry=await vaistoText.inner_text()
    #print(dataEntry)
    vaistoInfo = await page.query_selector("css=div.accordionTab__content")
    vaistoInfo = await vaistoInfo.inner_text()
    ##\37 492 > div:nth-child(3) > div > div.col.mb-4 > div:nth-child(1) > div.accordionTab__content > div > div > span
    
    medicine_info = split_medicine_info(dataEntry)
    if medicine_info is None:
        print(f"Could not parse medicine info from: {dataEntry}")
        return None
    try:
        vaistoInfo=ReturnVaistoVartojimas(vaistoInfo)
        medicine_info["tipas"] = Receptas
        medicine_info["kaina"] = await vaistoKaina.inner_text()
        medicine_info["vaistine"] = "Eurovaistine"
        medicine_info["url"] = url
        medicine_info["vartojimoInstrukcijos"] = vaistoInfo
        update_excel_file(medicine_info)
    except Exception as e:
        print(f"Error processing inside EuroReceptiniaiVaista item: {dataEntry}, Error: {e}")
    return None

async def GintarasGetPageItems(page):
    baseURL="https://www.gintarine.lt"
    urlList = []
    items = await page.query_selector_all("css=#product-container > div > div > form")
    ###product-container > div > div > form:nth-child(1)
    print(f"Found {len(items)} items on the page.")
    for item in items:
        
        #vaistoText = await item.query_selector("css=div.product__title > a")
        ##product-container > div > div > form:nth-child(1) > div > div.product__container-details > div.product__title > a
        #vaistoKaina = await item.query_selector("css=div.product__price > span")
        ##product-container > div > div > form:nth-child(1) > div > div.product__container-actions > div.product__price > span.product__price--regular
        vaistoURL = await item.query_selector("css=div.product__title > a")
        vaistoURL = await vaistoURL.get_attribute("href")
        #dataEntry=await vaistoText.inner_text()
        #vaistoInfo = await item.query_selector("css=div.single-product__body > div.single-product__details")
        #print(vaistoInfo)
        #vaistoInfo = await vaistoInfo.inner_text()
        
        #body > div.master-wrapper-page > div.ColumnsOneFull.container-root > div.container-fw > div > main > div.single-product__right > div > div.single-product__body > div.single-product__details
        
        #print(dataEntry)
        #medicine_info = split_medicine_info(dataEntry)
        #print(medicine_info)
        
        try:
            #medicine_info["tipas"] = "Receptinis vaistas"
            #medicine_info["kaina"] = await vaistoKaina.inner_text()
            #medicine_info["vaistine"] = "GintarineVaistine"
            #medicine_info["url"] = baseURL+vaistoURL
            url = urljoin(baseURL, vaistoURL)
            #vaistoInfo=ReturnVaistoVartojimas(vaistoInfo)
            #medicine_info["vartojimoInstrukcijos"] = vaistoInfo
            #update_excel_file(medicine_info)
        except Exception as e:
            #print(f"Error processing GintarasGetPageItems item: {dataEntry}, Error: {e}")
            continue
        urlList.append(url)
    return urlList

async def GintarineGetVaistai(page,url):
    vaistoText = await page.query_selector("css=div.single-product__head > h1")
    #body > div.master-wrapper-page > div.ColumnsOneFull.container-root > div.container-fw > div > main > div.single-product__right > div > div.single-product__head > h1
    vaistoKaina = await page.query_selector("css=div.single-product__price")
    ##product-details-form > div.single-product__price > div > div.price-val.price-value-41159
    dataEntry=await vaistoText.inner_text()
    #print(dataEntry)
    vaistoInfo = await page.query_selector("css=div.single-product__details-description > div.accordion__content")
    vaistoInfo = await vaistoInfo.inner_text()
    #body > div.master-wrapper-page > div.ColumnsOneFull.container-root > div.container-fw > div > main > div.single-product__right > div > div.single-product__body > div.single-product__details > div > div.single-product__details-description > div.accordion__content
    
    medicine_info = split_medicine_info(dataEntry)
    if medicine_info is None:
        print(f"Could not parse medicine info from: {dataEntry}")
        return None
    try:
        vaistoInfo=ReturnVaistoVartojimas(vaistoInfo)
        medicine_info["tipas"] = "Receptinis vaistas"
        medicine_info["kaina"] = await vaistoKaina.inner_text()
        medicine_info["vaistine"] = "GintarineVaistine"
        medicine_info["url"] = url
        medicine_info["vartojimoInstrukcijos"] = vaistoInfo
        update_excel_file(medicine_info)
    except Exception as e:
        print(f"Error processing inside EuroReceptiniaiVaista item: {dataEntry}, Error: {e}")
    return None

async def RunBrowser(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await StartUp(browser)
        
        page= await  GoToSite(url,context)
        page_count = await GetPageCount(page)
        page_count = int(await page_count.inner_text())
        
        urlList = []
        for i in range(1,page_count+1):
        #for i in range(1, 2):  # Change range to 3 for testing
            print(i)
            url = f"https://www.eurovaistine.lt/vaistai-nereceptiniai?page="+str(i)
            page=await GoToSite(url,context)
            urlList.append(await EuroGetPageItems(page))
        
        urlListUpdated=[]
        for urlListItem in urlList:
            for itemURL in urlListItem:
                urlListUpdated.append(itemURL)

                page = await GoToSite(itemURL, context)
                print(f"Processing URL: {itemURL}")
                await EuroReceptiniaiVaistai(page, itemURL,"Nereceptinis vaistas")

        print(f"Total URLs collected: {len(urlListUpdated)}")
        
        ABC = list(string.ascii_uppercase)
        urlPart1="https://www.eurovaistine.lt"
        for letter in ABC:
            url = "https://www.eurovaistine.lt/vaistai-skirti-gydytojo?letter=" + letter
            page = await GoToSite(url, context)
            itemsInPage = await page.query_selector_all("css= div.rxList__wrapper > div > a")
            ##sfreact-reactRenderer6831ab43cb3710\.45348189 > div > div > div.rxList__wrapper > div:nth-child(2) > a
            print(f"Found {len(itemsInPage)} items on the page for letter {letter}.")
            urlList= []
            for item in itemsInPage:
                itemURL= await item.get_attribute("href")
                itemURL = urlPart1 + itemURL
                #print(itemURL)
                urlList.append(itemURL)
            for itemURL in urlList:
                itemPage = await GoToSite(itemURL, context)
                await EuroReceptiniaiVaistai(itemPage,itemURL)
        
        url="https://www.gintarine.lt/receptiniai-vaistai"
        page = await GoToSite(url, context)
        pageCount=await GetPageCount2(page)
        urlList = []
        for i in range(1,int(pageCount)+1):
        #for i in range(1, 2):  # Change range to 3 for testing
            url = f"https://www.gintarine.lt/receptiniai-vaistai?pagenumber={i}"
            page = await GoToSite(url, context)
            urlList.append(await GintarasGetPageItems(page))
            
        urlListUpdated=[]
        for urlListItem in urlList:
            for itemURL in urlListItem:
                urlListUpdated.append(itemURL)

                page = await GoToSite(itemURL, context)
                print(f"Processing URL: {itemURL}")
                await GintarineGetVaistai(page, itemURL)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(RunBrowser(url))
    