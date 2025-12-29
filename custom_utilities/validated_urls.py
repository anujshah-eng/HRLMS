import requests

def get_accessible_urls(urls):
    accessible = []
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                accessible.append(url)
        except:
            pass
    return accessible