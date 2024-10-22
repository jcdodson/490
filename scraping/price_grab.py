import requests
import time
import psycopg2
from psycopg2 import sql

headers = {
    'User-Agent': 'OSRS price predictor, discord:hemoglobinbadboy'
}

def fetch_item_ids_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT item_id FROM items;")
    item_ids = cursor.fetchall()
    cursor.close()
    return [item[0] for item in item_ids]

def fetch_timeseries_data(item_id):
    url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=24h&id={item_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()['data']
    else:
        print(f"Failed to fetch timeseries data for item_id {item_id}. Status code: {response.status_code}")
        return None

def insert_daily_prices_to_db(conn, item_id, daily_prices):
    cursor = conn.cursor()

    for price_entry in daily_prices:
        avg_price = price_entry.get('avgHighPrice', None)
        timestamp = price_entry['timestamp']

        if avg_price is not None:
            query = """
                INSERT INTO item_prices (item_id, avg_price, price_check_date)
                VALUES (%s, %s, to_timestamp(%s))
            """
            cursor.execute(query, (item_id, avg_price, timestamp))

    conn.commit()
    cursor.close()

def main():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="BlackDahn24!",
            host="osrs-item-db.cnpvs58a5rer.us-west-1.rds.amazonaws.com",
            port="5432"
        )
        item_ids = fetch_item_ids_from_db(conn)
        if not item_ids:
            print("No item IDs found in the database.")
            return

        for item_id in item_ids:
            print(f"Processing item_id: {item_id}")

            daily_prices = fetch_timeseries_data(item_id)
            if daily_prices:
                insert_daily_prices_to_db(conn, item_id, daily_prices)

            time.sleep(1)

    except Exception as error:
        print(f"Error: {error}")

    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
