# Foreign Exchange Trading Simulation
## Overview
This project was developed for a programming challenge competition. The objective was to create a foreign exchange (forex) trading bot capable of executing trades on a simulated exchange market. My implementation leverages the Exponential Moving Average (EMA) strategy to analyse market trends and make trade decisions.

## Features
- **EMA Trading Strategy**: The bot uses a dual EMA crossover technique to identify potential buy and sell signals based on market conditions.
- **Market Data via API**: The challenge provided an API to access real-time market data for the EUR/GBP currency pair, which the bot uses to analyse and execute trades.
- **Simulated Market Environment**: All trading decisions are tested and executed in a simulated forex market to assess the bot's performance in real-world-like conditions.
- **Risk Management**: Includes features such as take-profit and stop-loss settings with a 2:1 risk-reward ratio, aiming to minimise potential losses while maximising gains.

## How it works
The bot continuously monitors the current market value of EUR/GBP using the provided API and calculates two EMAs (short-term and long-term). A crossover of the short-term EMA above the long-term EMA generates a buy signal, while a crossover below generates a sell signal. The bot then adjusts positions based on the chosen strategy parameters.

## Team Participants:
- [Raul Blanco Vazquez](https://www.linkedin.com/in/raulblancovazquez/)
- [Zara Hussain](https://www.linkedin.com/in/zara-hussain-b0229b208/)
- [Zeeshan Masood](https://www.linkedin.com/in/zeeshan-masood/)