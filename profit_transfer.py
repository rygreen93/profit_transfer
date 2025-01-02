import argparse
import csv
import json
from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError
import schedule
import time
from datetime import datetime
import uuid
import logging
import traceback  # Add this if not already imported

# Add this new function for transferring from Unified to Funding
async def transfer_from_unified_to_funding(bot, coin: str, amount: float):
    transferred = None
    try:
        transferred = await bot.cc.private_post_v5_asset_transfer_inter_transfer(
            params={
                "transferId": str(uuid.uuid4()),
                "coin": coin,
                "amount": str(amount),
                "fromAccountType": "UNIFIED",
                "toAccountType": "FUND",
            }
        )
        return transferred
    except Exception as e:
        logging.error(f"Error transferring from unified to funding: {e}")
        traceback.print_exc()
        return None

# Create an argument parser for command-line options
parser = argparse.ArgumentParser(description='Script to periodically log trades and transfer a percentage of profit.')
parser.add_argument('-p', '--percentage', type=float, default=20,
                    help='Percentage of profit to transfer (e.g., 20 for 20%).')
args = parser.parse_args()

# Utility function to format the current UTC time for logging
def current_utc_time():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

def get_last_successful_execution_time(log_file_path):
    try:
        with open(log_file_path, 'r') as file:
            lines = file.readlines()
            last_line = lines[-1].strip()
            if last_line and not last_line.startswith('updatedTime'):
                last_execution_time = last_line.split(',')[0]
                last_execution_time = datetime.strptime(last_execution_time, '%Y-%m-%d %H:%M:%S')
                return int(last_execution_time.timestamp() * 1000)
        # Default return if file is empty or the last line starts with 'updatedTime' (header)
        return round((time.time() - 3600) * 1000)
    except (FileNotFoundError, IndexError):
        return round((time.time() - 3600) * 1000)

def log_last_hour_trades_and_total_profit(session, log_file_path, start_time):
    try:
        one_hour_ago_utc_ms = round((time.time() - 3600) * 1000)

        all_trades_response = session.get_closed_pnl(
            category="linear",
            start_time=start_time
        )

        all_trades = all_trades_response.get('result', {}).get('list', [])
        trades_since_last_success = [
            trade for trade in all_trades if int(trade['updatedTime']) >= one_hour_ago_utc_ms
        ]

        total_profit_since_last_success = sum(float(trade['closedPnl']) for trade in trades_since_last_success)

        with open(log_file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            for trade in trades_since_last_success:
                writer.writerow([
                    datetime.utcfromtimestamp(int(trade['updatedTime']) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    trade['symbol'],
                    trade['closedPnl'],
                    trade['orderId']
                ])

        return total_profit_since_last_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def transfer_profit(session, amount):
    try:
        # Round the amount to two decimal places
        rounded_amount = round(amount, 2)
        transfer_id = str(uuid.uuid4())

        # Use the new Unified to Funding transfer logic
        response = session.create_internal_transfer(
            transferId=transfer_id,
            coin="USDT",  # Change to the correct coin symbol
            amount=str(rounded_amount),  # Use rounded amount as a string
            fromAccountType="UNIFIED",
            toAccountType="FUND"
        )
        if response['retCode'] == 0:
            return response['result']['transferId']
        else:
            print(f"Failed to create internal transfer: {response['retMsg']}")
            return None

    except InvalidRequestError as e:
        print(f"An error occurred during the internal transfer: {e}")
        return None


def log_profit_transfer(log_file_path, transfer_time, symbol, closed_pnl, transaction_id):
    with open(log_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([transfer_time, symbol, closed_pnl, transaction_id])

def job():
    current_time = current_utc_time()
    start_time = get_last_successful_execution_time(log_file_path)
    total_profit = log_last_hour_trades_and_total_profit(session, log_file_path, start_time)
    if total_profit is not None:
        transfer_amount = round(total_profit * (args.percentage / 100), 2)
        if transfer_amount > 0:
            transaction_id = transfer_profit(session, transfer_amount)
            if transaction_id:
                transfer_time = current_utc_time()
                log_profit_transfer(profit_transfer_log_path, transfer_time, 'USDT', transfer_amount, transaction_id)
                print(f"{current_time}: Profit transfer of ${transfer_amount:.2f} ({args.percentage}%) - successful")
            else:
                print(f"{current_time}: Profit transfer failed")
        else:
            print(f"{current_time}: Nothing to transfer")
    else:
        print(f"{current_time}: Error calculating profit. No transfer attempted.")

if __name__ == "__main__":
    # Load API credentials from config.json
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
        api_key = config.get("api_key")
        api_secret = config.get("api_secret")

    # Initialize the HTTP session with Bybit's API
    session = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

    # File paths for logs
    log_file_path = 'last_hour_trades.csv'
    profit_transfer_log_path = 'profit_transfers.csv'

    # Ensure log files exist and have headers
    for file_path, headers in [
        (log_file_path, ['updatedTime', 'symbol', 'closedPnl', 'orderId']),
        (profit_transfer_log_path, ['transferTime', 'symbol', 'amount', 'transactionId']),
    ]:
        try:
            with open(file_path, 'x', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
        except FileExistsError:
            pass

    # Run the job immediately
    job()

    # Schedule the job to run every hour
    schedule.every().hour.do(job)

    # Run the pending jobs in a loop
    while True:
        schedule.run_pending()
        time.sleep(1)
