import os
import requests

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
BASE_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def list_databases():
    """List all databases accessible to the integration."""
    url = f"{BASE_URL}/search"
    payload = {"filter": {"value": "database", "property": "object"}}
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json().get("results", [])

def query_database(database_id):
    """Retrieve all rows from a specific Notion database (paginated)."""
    url = f"{BASE_URL}/databases/{database_id}/query"
    all_results = []
    payload = {}
    while True:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        all_results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data.get("next_cursor")
    return all_results

def list_pages():
    """List all standalone pages accessible to the integration."""
    url = f"{BASE_URL}/search"
    payload = {"filter": {"value": "page", "property": "object"}}
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json().get("results", [])

def retrieve_all_data():
    """Retrieve all pages and database entries in the workspace."""
    all_data = {"databases": {}, "pages": []}

    # Get all databases
    databases = list_databases()
    for db in databases:
        db_id = db["id"]
        db_title = db.get("title", [{}])[0].get("plain_text", "Untitled")
        print(f"Retrieving data from database: {db_title}")
        all_data["databases"][db_id] = {
            "title": db_title,
            "entries": query_database(db_id)
        }

    # Get all standalone pages
    pages = list_pages()
    for p in pages:
        all_data["pages"].append(p)

    return all_data

if __name__ == "__main__":
    data = retrieve_all_data()
    print(f"Retrieved {len(data['databases'])} databases and {len(data['pages'])} pages.")
