import requests
import sys
import psycopg2
import json

headers = {'User-Agent': 'OSRS price predictor, discord:hemoglobinbadboy'}

def save_mapping_to_file(mapping, file_path):
        try:
                with open(file_path, 'w') as file:
                        json.dump(mapping, file, indent=4)
                print(f"Item mapping successfully saved to {file_path}")
        except Exception as error:
                print(f"Error saving item mapping to file: {error}")

def fetch_item_map():
        url = "https://prices.runescape.wiki/api/v1/osrs/mapping"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
                items = response.json()
                item_mapping = {item['name'].lower(): item['id'] for item in items}
                print("Fetched and created map")
                return item_mapping
        else:
                print(f"Failed to fetch item mapping. Status code: {response.status_code}")
                return {}

def get_item_id(item_name, item_mapping):
        return item_mapping.get(item_name.lower())

def insert_item_to_db(conn, item_name, item_id):
        if conn:
                cursor = conn.cursor()
                try:
                        query = """
                                INSERT INTO items (item_name, item_id)
                                VALUES (%s, %s)
                                ON CONFLICT (item_id) DO NOTHING;
                        """
                        cursor.execute(query, (item_name, item_id))
                        conn.commit()
                        print(f"Inserted {item_name} with ID {item_id} into the database.")
                except Exception as error:
                        print(f"Error inserting {item_name} into the database: {error}")
                finally:
                        cursor.close()

def process_items(conn, item_names):
        item_mapping = fetch_item_map()
        if not item_mapping:
                print("Error: could not retrieve item map")
                return

        save_mapping_to_file(item_mapping, 'item_mapping.txt')

        for item_name in item_names:
                item_id = get_item_id(item_name, item_mapping)
                if item_id is not None:
                        insert_item_to_db(conn, item_name, item_id)
                else:
                        print(f"Item '{item_name}' not found in mapping.")

def read_item_names_from_file(file_path):
        try:
                with open(file_path, 'r') as f:
                        item_names = [line.strip() for line in f.readlines()]
                        return item_names
        except FileNotFoundError:
                print(f"Error: File '{file_path}' not found.")
                return []

def insert_hc_item(conn):
        if conn:
                cursor = conn.cursor()
                try:
                        item_name = 'Abbysal whip'
                        item_id = 4151

                        query = """
                                INSERT INTO items (item_name, item_id)
                                 VALUES (%s, %s)
                                 ON CONFLICT (item_id) DO NOTHING;
                                """
                        cursor.execute(query, (item_name, item_id))
                        conn.commit()
                        print(f"Inserted {item_name} with ID {item_id} into the database.")
                except Exception as error:
                        print(f"Error inserting {item_name} into the database: {error}")
                finally:
                        cursor.close()

def test(conn):
        if conn:
                cur = conn.cursor()
                try:
                        cur.execute("""SELECT * FROM items""")
                        rows = cur.fetchall()
                        for row in rows:
                                print(row)
                except Exception as error:
                        print(error)
                finally:
                        cur.close()

def main():
        if len(sys.argv) != 2:
                print("Usage: python3 id_grabber.py <item_names_file>")
                return

        item_file = sys.argv[1]
        item_names = read_item_names_from_file(item_file)
        if not item_names:
                print("No items to process")
                return

        connection = None
        try:
                connection = psycopg2.connect(
                        dbname="postgres",
                        user="postgres",
                        password="BlackDahn24!",
                        host="osrs-item-db.cnpvs58a5rer.us-west-1.rds.amazonaws.com",
                        port="5432"
                )
                process_items(connection, item_names)
                
        except Exception as error:
                print(f"Error connecting to the database: {error}")
        finally:
                if connection:
                        connection.close()
                        print("Connection closed.")

if __name__ == "__main__":
        main()

