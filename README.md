# Evaluating The Value of Social Media Sentiment
Imagine that we're investigating a potential new vendor called Social Media Sentiment (SMS). They
promise to give us a daily file that will tell us for a given stock ticker how many people were tweeting
about that ticker, and how many of those tweets were positive. A researcher wants to determine if
there's any value in this data set, and have asked you to provide them with the historical sentiment
data, as well as some data about the stock returns, specifically open, close, and ex-dividend values.

1. Unzip and parse the files provided by the vendor.
2. Parse the stock return data provided.
3. For every date ticker pair that SMS provide data for, try to map that row to a row in the
returns data. The researcher has no interest in rows from return data that don’t map to a
row from SMS, but rows from SMS that don’t map to return values may still be of interest.
4. Write the data into a SQLite database.

## Requirements
1. Python3: https://www.python.org/downloads/release
2. After you've installed python3 (it comes with pip) install pipenv from the commandline like so: `pip install pipenv`
3. Unzip the package in which this zip resides into a directory (label it PDIR)
4. execute `pipenv install PDIR` from the commandline, where PDIR is replaced with the location of the unzipped package. 

## Installation
```bash
pipenv install -e PDIR
pipenv shell
```
As before replace with the directory that the package was unzipped into. 
After executing the commands you will be in the shell of a virtual environment with the package installed in it. 

## Usage
* To see usage information `main` or `main -h`
* To generate a database run for example `main --price-data data/in/price_data.csv --sms-data-dir data/in/sms_data/` where the paths are relative to the directory unzipped into, and contain the data passed as part of this test. Adjust these parameters as appropriate for the local environment.
* (Python API (a)) To query a date range for a ticker symbol execute for example `main --tquery XCOM:2017-01-01:2017-01-02` this will print a sub-matrix to stdout from the merged table requested. The sub-matrix represents all rows from ticker symbol XCOM between 2017-01-01 and 2017-01-02.
* (Python API (b)) To query all rows of the merged matrix for a particular date execute for example `main --dquery 2017-01-02`, this will give all rows of the merge matrix on 2017-01-02.

## Deliverables
1. This README document is part of zip file containing my code for this project. The database requested can be found in `data/out/data.db`.
2. Issues: The last 3 months worth of sms files have the date format YYYYMMDD whereas all the other files have the date format YYYY-MM-DD. The file headers of the sms files have mislabeled the `date` column as `daet`. Some values in the sms files use comma delimiters within numbers throwing off the csv format, for example the number 1234 can be represented 1,234. Many of the rows in the sms files contain a NaN value for the 'tweets' column, I removed rows like this while reading these files, such rows are dropped and not in the merged database.
3. Counts: In total there are 3072910 rows in the merged database. I found 302 suspect rows in the database, these rows have ticker symbol 'symbol' I did not look for some pattern in why this was going on, but it seems unlikely that 'symbol' is a legitimate stock ticker symbol, so the rows are suspect.  
4. Comments/Questions: Dear vendor, what's up with 'symbol'? What is that supposed to be? It's weird for an error, it looks like the result of a bad merge from other data, but that's just speculation. What are the NaNs supposed to be? 0s? Why aren't they 0 then? Is it because the number was too big? Design decision question: I dropped the NaN rows, is there something better I could have done?
