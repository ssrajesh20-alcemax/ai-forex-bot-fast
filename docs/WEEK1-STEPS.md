# AI Forex Bot – Week 1 Implementation Steps

## 1. Clone the repo and prepare directories:
   - git pull
   - mkdir -p data/logs

## 2. Install dependencies:
   - pip install -r requirements.txt

## 3. Update config.py locally (do not commit secrets):
   - Add your rotated Telegram bot token and chat_id to the telegram section.

## 4. Start the API:
   - uvicorn api:app --reload

## 5. Test endpoints:
   - http://127.0.0.1:8000/health
   - http://127.0.0.1:8000/analyze?pairs=GBPUSD,EURUSD,USDJPY,AUDUSD,USDCAD,USDCHF,NZDUSD&tf=5m
   - and repeat for tf=15m and tf=4h

## 6. Tuning:
   - If alerts are too frequent, raise confidence_min in config.py from 75 to 80–85.
   - Confirm Telegram alerts are received when direction is BUY/SELL, confidence >= 75, RR >= 1.5

## 7. Next week:
   - Prepare to automate with n8n, connect economic calendar, add logging to Sheets, and wire in sentiment/MTF modifiers.

---
This content reflects all key plans, the value stack, and precise step-by-step instructions needed, as per the user's detailed instructions and requests.
