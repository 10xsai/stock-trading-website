# stock-trading-website

## Overview
A Stock Trading web application where users can buy stocks, sell stocks and view their past transactions.This application has User Authentication.Users can Signup, signin and reset their passwords.

Real time stock price information is obtained through an api key from IEX cloud.


## Installation

1. clone this repository using git command

```bash
$ git clone https://github.com/krishnagottipalli/stock-trading-website.git
```

2. create a virtual environment
```bash
$ cd project
$ python3 -m venv env
```

3. activate the virtual environment
```bash
$ source env/bin/activate
```

3. install flask
```python
$ pip install flask
```

4. initial setup
```python
$ export FLASK_APP=application.py
$ export FLASK_ENV=development
$ export API_KEY={ api_key }
```

5. run the application
```python
flask run
```
