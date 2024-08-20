import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time
import logging
import os
import configparser

# Konfiguráció betöltése
config = configparser.ConfigParser()
config.read('config.ini')

# Logging beállítása
logging.basicConfig(level=config['DEFAULT']['log_level'],
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Adatbázis fájl neve és elérési útja
DB_NAME = config['DEFAULT']['db_name']
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)

def create_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  source TEXT,
                  query_time TEXT,
                  insert_time TEXT,
                  title TEXT,
                  UNIQUE(source, title))''')
    conn.commit()
    return conn

def fetch_webpage(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_titles_444(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    titles = []

    title_elements = soup.find_all(['h1', 'header'], class_=['_1tm224b4', 'item__title'])

    for element in title_elements:
        a_tag = element.find('a')
        if a_tag and a_tag.string:
            title = a_tag.string.strip()
            titles.append(title)

    return titles

def extract_titles_index(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    titles = []

    title_elements = soup.find_all('h2', class_='cikkcim')

    for element in title_elements:
        a_tag = element.find('a')
        if a_tag and a_tag.string:
            title = a_tag.string.strip()
            titles.append(title)

    return titles


def save_to_database(conn, source, titles):
    c = conn.cursor()
    query_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    new_articles_count = 0

    for title in titles:
        insert_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        try:
            c.execute("INSERT INTO articles (source, query_time, insert_time, title) VALUES (?, ?, ?, ?)",
                      (source, query_time, insert_time, title))
            new_articles_count += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    return new_articles_count

def print_database_info():
    logging.info(f"SQLite adatbázis elérési útja: {DB_PATH}")
    logging.info("SQLite csatlakozási parancs:")
    logging.info(f"sqlite3 {DB_PATH}")
    logging.info("SQLite GUI kliensekkel (pl. DB Browser for SQLite) is megnyitható.")

def show_recent_articles():
    limit = int(config['DISPLAY']['recent_articles_limit'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT source, insert_time, title FROM articles ORDER BY insert_time DESC LIMIT ?", (limit,))
    articles = c.fetchall()
    conn.close()

    logging.info(f"Legutóbbi {limit} cikk:")
    for article in articles:
        logging.info(f"{article[0]} - {article[1]} - {article[2]}")

def scrape_website(conn, source, url, extract_function):
    try:
        html_content = fetch_webpage(url)
        titles = extract_function(html_content)

        if not titles:
            logging.warning(f"Nem sikerült címeket kinyerni a(z) {source} oldalból.")
            logging.debug(f"HTML tartalom: {html_content[:500]}...")

        new_articles = save_to_database(conn, source, titles)

        logging.info(f"{source} adatok frissítve. Új cikkek száma: {new_articles}")

    except Exception as e:
        logging.error(f"Hiba történt a(z) {source} oldal scrape-elése során: {str(e)}", exc_info=True)

def main():
    conn = create_database()
    print_database_info()

    websites = {
        '444': (config['444']['url'], extract_titles_444),
        'INDEX': (config['INDEX']['url'], extract_titles_index)
    }

    while True:
        for source, (url, extract_function) in websites.items():
            if config[source.upper()].getboolean('enabled'):
                scrape_website(conn, source, url, extract_function)

        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM articles")
        total_articles = c.fetchone()[0]
        logging.info(f"Összes cikk az adatbázisban: {total_articles}")

        show_recent_articles()

        time.sleep(int(config['DEFAULT']['refresh_interval']))

if __name__ == "__main__":
    main()
