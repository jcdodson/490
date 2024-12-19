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
            return render(request, 'myapp/search_results.html', {'error_message': "Please enter an item name to search."})

        try:
            #connect to db
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="BlackDahn24!",
                host="osrs-item-db.cnpvs58a5rer.us-west-1.rds.amazonaws.com",
                port="5432"
            )

            #strip user input
            item_name = item_name.strip()

            #db query for items
            cursor = conn.cursor()
            cursor.execute("""
                SELECT item_id, item_name FROM items 
                WHERE TRIM(item_name) ILIKE %s;
            """, (f"%{item_name}%",))  #case-insensitive with partial match

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            if not results:
                #render the search results page with an error message
                return render(request, 'myapp/search_results.html', {
                    'error_message': "No items found",
                    'results': None
                })

            if len(results) == 1:
                #redirect directly to the price graph
                item_id = results[0][0]
                return redirect('price_graph', item_id=item_id)

            #if multiple results, render the search results page with the items
            return render(request, 'myapp/search_results.html', {'results': results})

        except Exception as e:
            return render(request, 'myapp/search_results.html', {'error_message': f"An error occurred: {str(e)}", 'results': None})


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


#price graph for a specific item based on its item_id
def price_graph(request, item_id):
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="BlackDahn24!",
            host="osrs-item-db.cnpvs58a5rer.us-west-1.rds.amazonaws.com",
            port="5432"
        )

        cursor = conn.cursor()

        #getting item_name
        cursor.execute("SELECT item_name FROM items WHERE item_id = %s;", (item_id,))
        item_name_result = cursor.fetchone()
        if not item_name_result:
            return HttpResponse("Item not found.")
        item_name = item_name_result[0]

        #define 30 day timeframe
        thirty_days_ago = timezone.now().date() - timedelta(days=30)

        #query price for last 30 days
        cursor.execute("""
            SELECT price_check_date, avg_price 
            FROM item_prices 
            WHERE item_id = %s AND price_check_date >= %s
            ORDER BY price_check_date;
        """, (item_id, thirty_days_ago))
        price_results30 = cursor.fetchall()

        #query trade data for last 30 days
        cursor.execute("""
            SELECT price_check_date, daily_traded 
            FROM item_trades 
            WHERE item_id = %s AND price_check_date >= %s
            ORDER BY price_check_date;
        """, (item_id, thirty_days_ago))
        trade_results30 = cursor.fetchall()

        seven_days_ago = timezone.now().date() - timedelta(days=7)

        #query price data for last 7 days
        cursor.execute("""
            SELECT price_check_date, avg_price 
            FROM item_prices 
            WHERE item_id = %s AND price_check_date >= %s
            ORDER BY price_check_date;
        """, (item_id, seven_days_ago))
        price_results7 = cursor.fetchall()

        #query trade data for last 7 days
        cursor.execute("""
            SELECT price_check_date, daily_traded 
            FROM item_trades 
            WHERE item_id = %s AND price_check_date >= %s
            ORDER BY price_check_date;
        """, (item_id, seven_days_ago))
        trade_results7 = cursor.fetchall()

        #get most recent scan info
        cursor.execute("""
            SELECT MAX(price_check_date)
            FROM item_prices;
        """)
        last_scanned_result = cursor.fetchone()
        last_scanned = last_scanned_result[0] if last_scanned_result[0] else None

        cursor.close()
        conn.close()

        if not price_results30:
            return HttpResponse("No price data available for this item.")
        if not trade_results30:
            return HttpResponse("No trade data available for this item.")
        #if not price_results7:
        #    return HttpResponse("No price7 data available for this item.")
        #if not trade_results7:
        #    return HttpResponse("No trade7 data available for this item.")

        #format scanned information
        if last_scanned:
            last_scanned = timezone.make_aware(last_scanned)
            time_since_last_scan = timezone.now() - last_scanned
            last_scanned_display = f"{time_since_last_scan.days} day(s) ago" if time_since_last_scan.days > 24 else "Today"
        else:
            last_scanned_display = "Never"

        #prepare datasets
        price_data30 = [{"date": row[0].strftime('%Y-%m-%d'), "price": float(row[1])} for row in price_results30]
        trade_data30 = [{"date": row[0].strftime('%Y-%m-%d'), "volume": int(row[1])} for row in trade_results30]
        price_data7 = [{"date": row[0].strftime('%Y-%m-%d'), "price": float(row[1])} for row in price_results7]
        trade_data7 = [{"date": row[0].strftime('%Y-%m-%d'), "volume": int(row[1])} for row in trade_results7]

        # Compute stats for 30 days
        avg_price_30 = round(mean([d[1] for d in price_results30]))
        high_price_30 = round(max([d[1] for d in price_results30]))
        low_price_30 = round(min([d[1] for d in price_results30]))
        total_traded_30 = sum([d[1] for d in trade_results30])

        # Compute stats for 7 days
        avg_price_7 = round(mean([d[1] for d in price_results7]))
        high_price_7 = round(max([d[1] for d in price_results7]))
        low_price_7 = round(min([d[1] for d in price_results7]))
        total_traded_7 = sum([d[1] for d in trade_results7])

        # Pass the stats to the template
        return render(request, 'myapp/price_graph.html', {
            'price_data30': json.dumps(price_data30),
            'trade_data30': json.dumps(trade_data30),
            'price_data7': json.dumps(price_data7),
            'trade_data7': json.dumps(trade_data7),
            'item_name': item_name,
            'last_scanned': last_scanned_display,
            'avg_price_30': avg_price_30,
            'high_price_30': high_price_30,
            'low_price_30': low_price_30,
            'total_traded_30': total_traded_30,
            'avg_price_7': avg_price_7,
            'high_price_7': high_price_7,
            'low_price_7': low_price_7,
            'total_traded_7': total_traded_7,
        })

    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")
        
def index(request):
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="BlackDahn24!",
            host="osrs-item-db.cnpvs58a5rer.us-west-1.rds.amazonaws.com",
            port="5432"
        )

        cursor = conn.cursor()

        cursor.execute("""
            SELECT MAX(price_check_date)
            FROM item_prices;
        """)
        last_scanned_result = cursor.fetchone()
        last_scanned = last_scanned_result[0] if last_scanned_result[0] else None

        if last_scanned:
            last_scanned = timezone.make_aware(last_scanned)
            time_since_last_scan = timezone.now() - last_scanned
            last_scanned_display = f"{time_since_last_scan.days} day(s) ago" if time_since_last_scan.days > 24 else "Today"
        else:
            last_scanned_display = "Never"

        #query for top items in last 30 days
        now = timezone.now().date()
        thirty_days_ago = now - timedelta(days=30)

        cursor.execute("""
            SELECT i.item_id, i.item_name, (MAX(p.avg_price) - MIN(p.avg_price)) AS price_change
            FROM items i
            JOIN item_prices p ON i.item_id = p.item_id
            WHERE p.price_check_date >= %s
            GROUP BY i.item_id, i.item_name
            ORDER BY price_change DESC
            LIMIT 3;
        """, (thirty_days_ago,))
        top_price_changes = cursor.fetchall()

        cursor.execute("""
            SELECT i.item_id, i.item_name, SUM(t.daily_traded) AS total_traded
            FROM items i
            JOIN item_trades t ON i.item_id = t.item_id
            WHERE t.price_check_date >= %s
            GROUP BY i.item_id, i.item_name
            ORDER BY total_traded DESC
            LIMIT 3;
        """, (thirty_days_ago,))
        top_traded_items = cursor.fetchall()

        cursor.close()
        conn.close()

        price_change_items = [
            {'id': item[0], 'name': item[1], 'price_change': item[2]}
            for item in top_price_changes
        ]

        traded_items = [
            {'id': item[0], 'name': item[1], 'total_traded': item[2]}
            for item in top_traded_items
        ]

        return render(request, 'myapp/home.html', {
            'top_items': price_change_items,
            'top_traded_items': traded_items,
            'last_scanned': last_scanned_display
        })

    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")