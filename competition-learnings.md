# Competition Learnings

### Dev guide

Jane street provides a `sample-bot.py` python code where we can do our coding.

The main methods required are:

- a general order function which takes in the information on whether to buy/sell
- basic trading strategy (eg. penny-pinching) which finds/takes the fair value and determine the value to buy/sell

(optional)

- a function to collect the current bid/ask price in the marketplace
  - this will help in finding the fair value of other stocks and ETF
- maths functions eg calculating fair value
- bash scripts to automatically copy the python file locally to remote and execute the python script
- function to process each message from marketplace and carry out the respective function

### Debugging

`ps aux | grep <bot-name>`  
`kill <port>`
