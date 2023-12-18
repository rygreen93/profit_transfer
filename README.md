# Profit Transfer Automation Script

## Introduction

This repository contains a Python script designed to automate the process of transferring profits from Derivatives to Spot accounts on Bybit. The script logs trades data, calculates total profit, and performs internal transfers according to the user's predefined percentage.

## Features

- Logs closed PnL trades from Bybit API.
- Calculates total profit since the last successful execution.
- Transfers a user-defined percentage of the profit from the Derivatives account to the Spot account.
- Logs internal transfer details.
- Handles API rate limiting and transfer errors gracefully.

## Prerequisites

Before running the script, ensure you have:

- Python 3.6 or later installed on your system.
- `pip` (Python package installer) for managing software packages.
- An account on Bybit with API key and secret.

## Installation

Clone the repository to your local machine using:

```bash
git clone https://github.com/rygreen93/profit_transfer.git
```

Navigate to the script directory:

```bash
cd your-repository-name
```

Install the required dependencies:

```bash
pip3 install -r requirements.txt
```

## Configuration

Create a `config.json` file in the root directory of the project with your Bybit API credentials:

```json
{
  "api_key": "your_api_key",
  "api_secret": "your_api_secret"
}
```

Ensure this file is added to your `.gitignore` to keep your credentials secure.

## Usage

Run the script with the following command:

```bash
python3 profit_transfer.py
```

To specify a percentage of the profit to transfer, use the `-p` argument:

```bash
python3 profit_transfer.py -p 20
```

This will transfer 20% of the profit. If no percentage is specified, the script defaults to transferring 20% of the profit.

## Logs

The script generates two log files:

- `last_hour_trades.csv`: Logs the trades data and calculated profit.
- `profit_transfers.csv`: Logs the details of the profit transfers.

Make sure these files are not uploaded to public repositories to keep your data secure.

## Contributing

Contributions to the script are welcome. Please ensure you follow best practices and submit a pull request for review.

## License

This script is licensed under the [MIT License](LICENSE).

Please note that this script interacts with financial accounts and should be used with caution. The authors are not responsible for any financial losses incurred through the use of this script.
```
