"""
Created on 09th of June 2022

@author: Serban


README:

Before running the script:

1. Go to EPPO website, create an account, login: https://data.eppo.int/
2. Copy the token and write in terminal:
export token='__your__token__from_eppo_website__'
"""
import requests
import lxml.html as lh
import pandas as pd
from typing import List
import os


def web_scraper_FAO(url, xpath) -> pd.DataFrame:
    """Gets the table from the xpath in a dataframe

    Args:
        url
        xpath

    Returns:
        pd.DataFrame: the table in a dataframe
    """
    # Create a handle, page, to handle the contents of the website
    page = requests.get(url)
    # Store the contents of the website under doc
    doc = lh.fromstring(page.content)
    # Parse data that are stored between <tr>..</tr> of HTML
    tr_elements = doc.xpath(xpath)
    # Get column name
    col = [" ".join(t.text_content().split()) for t in tr_elements[0]]
    # Create df
    df = pd.DataFrame(columns=col)

    # Append to the dataframe
    for j in range(1, len(tr_elements)):
        row = [" ".join(t.text_content().split()) for t in tr_elements[j]]
        df.loc[len(df)] = row  # type: ignore
    return df


def prefnames2codes(latin_name: str) -> str:
    """returns the EPPO code for a latin name. If no eppo code is found for the species, returns the eppo code for the genus

    Args:
        latin_name (str): the latin name of the plant/pest/disease

    Returns:
        str: EPPO code
    """
    token = os.getenv("token")
    API_ENDPOINT = "https://data.eppo.int/api/rest/1.0" + "/tools/prefnames2codes"

    # Pre-processing the latin name
    if ";" in latin_name:
        latin_name = latin_name.split(";", 1)[0]
    if " spp" in latin_name:
        latin_name = latin_name.split(" spp", 1)[0]

    datas = {"authtoken": token, "intext": latin_name}
    r = requests.post(url=API_ENDPOINT, data=datas)

    if r.status_code == 200:
        r = r.json()
        if "NOT FOUND" not in r["response"]:
            return r["response"]
        else:
            latin_name = latin_name.split(" ", 1)[0]
            datas = {"authtoken": token, "intext": latin_name}
            r = requests.post(url=API_ENDPOINT, data=datas)
            if r.status_code == 200:
                r = r.json()
                return r["response"]
    return "Error connecting to EPPO API"


def generate_crops_eppo_csv(is_test=False):
    """create the csv taking the main crops from the FAO website and the EPPO code from the EPPO API"""

    url = "https://www.fao.org/economic/the-statistics-division-ess/world-census-of-agriculture/programme-for-the-world-census-of-agriculture-2000/appendix-3-alphabetical-list-of-crops-botanical-name-and-code-number/en/"
    xpath = "//*[@id='content-elements']/table/tbody/tr"
    df = web_scraper_FAO(url, xpath)
    if is_test == True:
        df = df.head(40)
    df["EPPO"] = df["BOTANICAL NAME"].apply(prefnames2codes)

    def clean_data(x):
        try:
            return x.split(";", 1)[1]
        except:
            return x

    df["EPPO"] = df["EPPO"].apply(lambda x: clean_data(x))

    df.to_csv(
        r"outcome/crops.csv",
        index=False,
        header=True,
    )
    # Human inspection will also be necessary to ensure data quality


# generate_crops_eppo_csv(is_test=True)
