#!/bin/bash

source /home/ubuntu/env/bin/activate
python3 /home/ubuntu/scraping/price_grab.py
python3 /home/ubuntu/scraping/trade_grab.py
deactivate
