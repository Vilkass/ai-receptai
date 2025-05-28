from playwright.async_api import async_playwright
import asyncio
import os
import pandas as pd
import re
import string
import time

savePath = "urpath/"

def ReadExcelFile():
    filename = savePath+"VaistaiSuInfoFinal.xlsx"
    if os.path.exists(filename):
        df = pd.read_excel(filename)
        return df
    else:
        print("File does not exist.")
        return pd.DataFrame()  # Return an empty DataFrame if the file does not exist
    
def update_excel_file(data, filename="VaistuInfoSuGeraisFeatures"):
    filename = savePath+filename+".xlsx"
    
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

def saveDFToExcel(df, filename="VaistuInfoSuGeraisFeatures"):
    filename = savePath+filename+".xlsx"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Save the DataFrame to Excel
    df.to_excel(filename, index=False, engine='openpyxl')

use_method_map = {
    'Vartoti per burną': 1,
    'Vartoti ant akių': 2,
    'Vartoti į nosį': 3,
    'Vartoti ant odos': 4,
    'Vartoti į burną ir ryklę': 5,
    'Vartoti į ausis': 6,
    'Įkvėpti': 8,
}

def get_use_method_id(method_text, method_map=use_method_map):
    
    
    method_text = method_text.strip().capitalize()
    if method_text in method_map:
        return method_map[method_text]
    else:
        # Assign the next available ID (lowest unused positive integer)
        existing_ids = set(method_map.values())
        new_id = 1
        while new_id in existing_ids:
            new_id += 1
        method_map[method_text] = new_id
        print("Updated use_method_map:")
        for k, v in sorted(method_map.items(), key=lambda x: x[1]):
            print(f"{v}: '{k}'")
        return new_id

drug_type_map = {
    'Nereceptinis vaistas': 1,
    'Receptinis vaistas': 2,
}

def get_drug_type_id(drug_type_text, drug_type_map=drug_type_map):
    if drug_type_text in drug_type_map:
        return drug_type_map[drug_type_text]

vaistine_map = {
    'GintarineVaistine': 1,
    'Eurovaistine': 2,
}
def get_vaistine_id(vaistine_text, vaistine_map=vaistine_map):
    if vaistine_text in vaistine_map:
        return vaistine_map[vaistine_text]

def CreateVaistiniuDiffrence(df):
    # Count occurrences of each href
    href_counts = df['vaprisHref'].value_counts()

    # Filter hrefs that appear 2 or more times
    duplicate_hrefs = href_counts[href_counts >= 2].index

    # Filter the original DataFrame to only include rows with duplicate hrefs
    duplicated_df = df[df['vaprisHref'].isin(duplicate_hrefs)][['vaistine', 'vaprisHref',"kaina"]]

    #saveDFToExcel(duplicated_df, filename="VaistinesInfo-sells")

    return duplicated_df

def DropHrefDuplicates(df):
    # Drop duplicate hrefs but keep the first occurrence
    df_no_duplicates = df.drop_duplicates(subset='vaprisHref', keep='first')
    return df_no_duplicates

def main():
    df = ReadExcelFile()
    newRow={}
    for index, row in df.iterrows():
        df.at[index, "vartojimoBudas"] = row["vartojimoBudas"].strip()
        df.at[index, "use_method_id"] = get_use_method_id(row["vartojimoBudas"])
        df.at[index, "vaistine"] = get_vaistine_id(row["vaistine"])
        df.at[index, "kaina"] = row["kaina"].replace("€", "").strip()
        df.at[index, "drug_type_id"] = get_drug_type_id(row["tipas"])
    sells_df = df[['vaistine', 'vaprisHref',"kaina"]]    
    #CreateVaistiniuDiffrence(df)
    df=DropHrefDuplicates(df)
    df["active_substance"]=df["veikliojiMedziagaText"]
    df["strength"]= df["dosage"]
    df["quantity"]=df["nscore"]
    df["paper"]=df["vaprisHref"]
    df.drop(columns=["url","full_text","vaistine","veikliojiMedziagaText","dosage","tipas","nscore","vaprisHref"], inplace=True)
    # Add new columns with default values
    df["medicine_id"] = range(33, 33 + len(df))
    df["formative_form_id"] = -1
    df["atc_code"] = "-1"
    df["atc_name"] = "-1"
    df["drug_subgroup_id"] = "null"
    df["base_price"] = "-1"

    df=df[["medicine_id","name","active_substance","strength","formative_form_id","use_method_id","drug_type_id","atc_code","atc_name","drug_subgroup_id","quantity","paper","base_price"]]
    
    # Replace vaprisHref in sells_df with corresponding medicine_id from df
    href_to_id = dict(zip(df["paper"], df["medicine_id"]))
    sells_df["vaprisHref"] = sells_df["vaprisHref"].map(href_to_id)

    saveDFToExcel(df, filename="ParuostaDataSQL")
    saveDFToExcel(sells_df, filename="VaistinesInfo-sells")

    # Save df to txt as SQL INSERT statements
    txt_filename = "C:/Users/Daiva/Desktop/Magistro darbas/Dirbtinio intelekto projektų valdymas/docker postgress/ParuostaDataSQL-inserts.txt"
    with open(txt_filename, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            values = []
            for val in row:
                if pd.isna(val) or val == "null" or val is None:
                    values.append("NULL")
                elif isinstance(val, str):
                    # Escape single quotes for SQL
                    values.append(f"'{val.replace('\'', '\'\'')}'")
                else:
                    values.append(str(val))
            insert_stmt = f"INSERT INTO medicine VALUES({', '.join(values)});"
            f.write(insert_stmt + "\n")

    # Save sells_df to txt as SQL INSERT statements
    sells_txt_filename = "C:/Users/Daiva/Desktop/Magistro darbas/Dirbtinio intelekto projektų valdymas/docker postgress/VaistinesInfo-sells-inserts.txt"
    with open(sells_txt_filename, "w", encoding="utf-8") as f:
        for idx, row in sells_df.iterrows():
            vaistine = row["vaistine"] if not pd.isna(row["vaistine"]) else "NULL"
            vaprisHref = row["vaprisHref"] if not pd.isna(row["vaprisHref"]) else "NULL"
            kaina = row["kaina"] if not pd.isna(row["kaina"]) else "NULL"
            if isinstance(kaina, str):
                kaina = kaina.replace(",", ".")
            # Remove quotes from vaistine and vaprisHref if they are strings

            # Compose the INSERT statement
            insert_stmt = f"INSERT INTO sells VALUES({vaistine}, {vaprisHref}, {kaina});"
            f.write(insert_stmt + "\n")
if __name__ == "__main__":
    print("Starting the feature extraction process...")
    main()