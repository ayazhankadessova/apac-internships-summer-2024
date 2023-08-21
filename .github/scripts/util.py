import json

from datetime import date, datetime, timezone, timedelta
import random
import os

# SIMPLIFY_BUTTON = "https://i.imgur.com/kvraaHg.png"
SIMPLIFY_BUTTON = "https://i.imgur.com/MXdpmi0.png"  # says apply
SHORT_APPLY_BUTTON = "https://i.imgur.com/w6lyvuC.png"
SQUARE_SIMPLIFY_BUTTON = "https://i.imgur.com/aVnQdox.png"
LONG_APPLY_BUTTON = "https://i.imgur.com/u1KNU8z.png"


def setOutput(key, value):
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        print(f"{key}={value}", file=fh)


def fail(why):
    setOutput("error_message", why)
    exit(1)


def getLocations(listing):
    locations = "</br>".join(listing["locations"])
    if len(listing["locations"]) <= 3:
        return locations
    num = str(len(listing["locations"])) + " locations"
    return f"<details><summary>**{num}**</summary>{locations}</details>"


def getDeadlines(listing):
    deadlines = "</br>".join(listing["deadline"])
    if len(listing["deadline"]) <= 3:
        return deadlines
    num = str(len(listing["deadline"])) + " deadlines"
    return f"<details><summary>**{num}**</summary>{deadlines}</details>"

def getCategory(listing):
    if listing["category"] == "Software Engineering":
        return "👩🏻‍💻🛠"
    elif listing["category"] == "DevOps":
        return "📊🎛️"
    elif listing["category"] == "Software Developer":
        return "👩🏻‍💻🖥️👩🏽‍💻"
    return ""


def getLink(listing):
    if not listing["active"]:
        return "🔒"
    link = listing["url"]
    if "?" not in link:
        link += "?utm_source=Simplify&ref=Simplify"
    else:
        link += "&utm_source=Simplify&ref=Simplify"
    # return f'<a href="{link}" style="display: inline-block;"><img src="{SHORT_APPLY_BUTTON}" width="160" alt="Apply"></a>'

    if listing["source"] != "Simplify":
        return f'<a href="{link}"><img src="{LONG_APPLY_BUTTON}" width="118" alt="Apply"></a>'

    simplifyLink = "https://simplify.jobs/p/" + listing["id"] + "?utm_source=GHList"
    return f'<a href="{link}"><img src="{SHORT_APPLY_BUTTON}" width="84" alt="Apply"></a> <a href="{simplifyLink}"><img src="{SQUARE_SIMPLIFY_BUTTON}" width="30" alt="Simplify"></a>'


def create_md_table(listings, offSeason=False):
    table = ""
    if offSeason:
        table += "| Company | Role | Location | Terms | Application/Link | Deadline | Start Date | Date Posted |\n"
        table += "| --- | --- | --- | --- | :---: | --- | --- | :---: |\n"
    else:
        table += "| Company | Role | Location | Application/Link | Deadline | Start Date | Date Posted |\n"
        table += "| --- | --- | --- |  :---: | --- | --- | :---: |\n"
    for listing in listings:
        company_url = listing["company_url"]
        company = listing["company_name"]
        company = (
            f"[{company}]({company_url})"
            if len(company_url) > 0 and listing["active"]
            else company
        )
        location = getLocations(listing)
        deadline = getDeadlines(listing)
        start_date = listing["start_date"]
        position = listing["title"] + getCategory(listing)
        terms = ", ".join(listing["terms"])
        link = getLink(listing)
        month = datetime.fromtimestamp(listing["date_posted"]).strftime("%b")
        dayMonth = datetime.fromtimestamp(listing["date_posted"]).strftime("%b %d")
        isBeforeJuly18 = datetime.fromtimestamp(listing["date_posted"]) < datetime(
            2023, 7, 18, 0, 0, 0
        )
        datePosted = month if isBeforeJuly18 else dayMonth
        if offSeason:
            table += f"| **{company}** | {position} | {location} | {terms} | {link} | {deadline} | {start_date} | {datePosted} |\n"
        else:
            table += f"| **{company}** | {position} | {location} | {link} | {deadline} | {start_date} | {datePosted} |\n"
        # table += f"| **{company}** | {location} | {position} | {link} | {status} | {datePosted} |\n"
    return table


def getListingsFromJSON(filename=".github/scripts/listings.json"):
    with open(filename) as f:
        listings = json.load(f)
        print("Recieved " + str(len(listings)) + " listings from listings.json")
        return listings


def embedTable(listings, filepath, offSeason=False):
    newText = ""
    readingTable = False
    with open(filepath, "r") as f:
        for line in f.readlines():
            if readingTable:
                if "|" not in line and "TABLE_END" in line:
                    newText += line
                    readingTable = False
                continue
            else:
                newText += line
                if "TABLE_START" in line:
                    readingTable = True
                    newText += (
                        "\n" + create_md_table(listings, offSeason=offSeason) + "\n"
                    )
    with open(filepath, "w") as f:
        f.write(newText)


def filterSummer(listings):
    return [
        listing
        for listing in listings
        if listing["is_visible"] and any("Summer" in item for item in listing["terms"])
    ]


def filterOffSeason(listings):
    return [
        listing
        for listing in listings
        if listing["is_visible"]
        and any(
            "Fall" in item or "Winter" in item or "Spring" in item
            for item in listing["terms"]
        )
    ]


def sortListings(listings):
    oldestListingFromCompany = {}
    linkForCompany = {}
    for listing in listings:
        date_posted = listing["date_posted"]
        if (
            listing["company_name"].lower() not in oldestListingFromCompany
            or oldestListingFromCompany[listing["company_name"].lower()] > date_posted
        ):
            oldestListingFromCompany[listing["company_name"].lower()] = date_posted
        if (
            listing["company_name"] not in linkForCompany
            or len(listing["company_url"]) > 0
        ):
            linkForCompany[listing["company_name"]] = listing["company_url"]

    def getKey(listing):
        date_posted = listing["date_posted"]
        date_updated = listing["date_updated"]
        return str(date_posted) + listing["company_name"].lower() + str(date_updated)

    listings.sort(key=getKey, reverse=True)

    for listing in listings:
        listing["company_url"] = linkForCompany[listing["company_name"]]

    return listings


def checkSchema(listings):
    props = [
        "source",
        "company_name",
        "id",
        "title",
        "active",
        "date_updated",
        "is_visible",
        "date_posted",
        "url",
        "locations",
        "company_url",
        "terms",
        "category",
        "deadline",
        "start_date",
    ]
    for listing in listings:
        for prop in props:
            if prop not in listing:
                fail(
                    "ERROR: Schema check FAILED - object with id "
                    + listing["id"]
                    + " does not contain prop '"
                    + prop
                    + "'"
                )
