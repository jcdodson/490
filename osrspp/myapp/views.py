from django.shortcuts import render, redirect
from django.http import HttpResponse
import psycopg2
import json
from statistics import mean
from datetime import timedelta
from django.utils import timezone

def search_item(request):
    if request.method == 'GET':
        item_name = request.GET.get('item_name')

        if not item_name:
            return HttpResponse("Please enter an item name to search.")

        try:
            #db connection
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="BlackDahn24!",
                host="osrs-item-db.cnpvs58a5rer.us-west-1.rds.amazonaws.com",
                port="5432"
            )

            #strip user input
            item_name = item_name.strip()

            #db query for the item_id based on the item _ame
            cursor = conn.cursor()
            cursor.execute("""
                SELECT item_id FROM items 
                WHERE TRIM(item_name) ILIKE %s;
            """, (f"%{item_name}%",))  #case-insensitive search with partial match

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if not result:
                return HttpResponse("Item not found.")

            item_id = result[0]

            #redirect to a dynamic URL to render the price graph for the item
            return redirect('price_graph', item_id=item_id)

        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")


def price_graph2(request, item_id):
    item_name = 'Example Item'
    
    data = [
        {'date': '2023-10-01', 'price': 100},
        {'date': '2023-10-02', 'price': 150},
        {'date': '2023-10-03', 'price': 120},
    ]
    
    #pass the item name and data to the template
    context = {
        'item_name': item_name,
        'data': json.dumps(data),
    }
    return render(request, 'myapp/price_graph.html', context)


# View to render the price graph for a specific item based on its item_id
def price_graph(request, item_id):
    try:
        #db connection
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="BlackDahn24!",
            host="osrs-item-db.cnpvs58a5rer.us-west-1.rds.amazonaws.com",
            port="5432"
        )

        cursor = conn.cursor()

        #get item_name
        cursor.execute("SELECT item_name FROM items WHERE item_id = %s;", (item_id,))
        item_name_result = cursor.fetchone()
        if not item_name_result:
            return HttpResponse("Item not found.")
        item_name = item_name_result[0]

        #db query to get historical prices
        cursor.execute("""
            SELECT price_check_date, avg_price 
            FROM item_prices 
            WHERE item_id = %s
            ORDER BY price_check_date;
        """, (item_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results:
            return HttpResponse("No data available for this item.")

        #converting data into JSON format for frontend use
        data = [{"date": row[0].strftime('%Y-%m-%d'), "price": float(row[1])} for row in results]

        #calcing the overall average price
        avg_price = float(mean([row[1] for row in results]))

        #data, item_name, and the average price passed to the template
        return render(request, 'myapp/price_graph.html', {
            'data': json.dumps(data),
            'avg_price': avg_price,
            'item_name': item_name
        })

    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")

def index(request):
    try:
        #db connection
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="BlackDahn24!",
            host="osrs-item-db.cnpvs58a5rer.us-west-1.rds.amazonaws.com",
            port="5432"
        )

        #getting current date and the date 30 days ago
        now = timezone.now().date()
        thirty_days_ago = now - timedelta(days=30)

        #query the top 3 items with the biggest average price change in the last 30 days
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.item_id, i.item_name, (MAX(p.avg_price) - MIN(p.avg_price)) AS price_change
            FROM items i
            JOIN item_prices p ON i.item_id = p.item_id
            WHERE p.price_check_date >= %s
            GROUP BY i.item_id, i.item_name
            ORDER BY price_change DESC
            LIMIT 3;
        """, (thirty_days_ago,))

        top_items = cursor.fetchall()
        cursor.close()
        conn.close()

        #data prepared to be passed to the template
        items = [{'id': item[0], 'name': item[1], 'price_change': item[2]} for item in top_items]

        #top 3 items passed to the template
        return render(request, 'myapp/home.html', {'top_items': items})

    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")