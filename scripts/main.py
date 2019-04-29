#!/usr/bin/env python
import logging, argparse, fileinput, sqlite3, pandas, sys, os, re
from sqlalchemy import create_engine
from datetime   import datetime
from bootstrap  import ROOT_DIR
float_dtype   = "float64"
int_dtype     = "int32"
date_fmt      = "%Y-%m-%d"
alt_date_fmt  = "%Y%M%d"

def mod_conf():
    logging.basicConfig(level=logging.INFO, format='<%(asctime)s-%(levelname)s> %(message)s')

def cli():
    parser = argparse.ArgumentParser()
    def is_file(maybe_file):
        if (os.path.isfile(maybe_file)):
            return os.path.realpath(maybe_file)
        else:
            raise argparse.ArgumentError("price-data must be csv file.")
    def is_dir(maybe_dir):
        if (os.path.isdir(maybe_dir)):
            return os.path.realpath(maybe_dir)
        else:
            raise argparse.ArgumentError("price-data must be directory.")
    def is_tquery(maybe_query):
        qargs = maybe_query.split(":")
        if( (len(qargs) !=3 ) ):
            raise argparse.ArgumentError("Incorrect query format.")
        ticker = str(qargs[0])
        dates = map(lambda x: datetime.strptime(x, date_fmt).date(), qargs[1:])
        return (ticker,) + tuple(dates)
    def is_dquery(maybe_query):
        date = datetime.strptime(maybe_query, date_fmt)
        return date.date()

    parser.add_argument("--price-data",
                        required=False,
                        help="the csv data for the price file.",
                        type=is_file)
    parser.add_argument("--sms-data-dir",
                        required=False,
                        help="the directory in which sms csv files live.",
                        type=is_dir)
    parser.add_argument("--dquery",
                        required=False,
                        help="query in the form YYYY-MM-DD representing the date of interest.",
                        type=is_dquery)
    parser.add_argument("--tquery",
                        required=False,
                        help="query in the form TICKER_SYMBOL:YYYY-MM-DD:YYYY-MM-DD where the dates repesent the timespan of interest.",
                        type=is_tquery)

    args = parser.parse_args()
    if( bool(args.price_data) != bool(args.sms_data_dir) ):
        raise TypeError("both price-data and sms-data-dir must be set to build the database.")
    if(args.dquery and args.tquery):
        raise TypeError("only one type of query may be launced per execution, either dquery or tquery, not both.")

    return args

def clean_up_file(file_path):
    with fileinput.FileInput(file_path, inplace=True, backup=".bak") as my_file:
        for line in my_file:
            out_line = line.replace("daet", "date")
            out_line = re.sub(r"(\d),(\d)", r"\1\2", out_line)
            print(out_line, end='')

def clean_up_sms_df(df):
    df = df[pandas.notnull(df["tweets"])]
    return df
        
def run(args):
    logging.info("begin {}".format(args))
    out_db_path = os.path.join(ROOT_DIR, "data", "out", "data.db")
    if(args.price_data):
        df_prices = pandas.read_csv(args.price_data, sep="|", skipinitialspace=True).reset_index(drop=True)
        df_prices["ticker"]      = df_prices["ticker"].astype("category")
        df_prices["date"]        = pandas.to_datetime(df_prices["date"], format=date_fmt).dt.date
        df_prices["open"]        = df_prices["open"].astype(float_dtype)
        df_prices["close"]       = df_prices["close"].astype(float_dtype)
        df_prices["high"]        = df_prices["high"].astype(float_dtype)
        df_prices["low"]         = df_prices["low"].astype(float_dtype)
        df_prices["ex-dividend"] = df_prices["ex-dividend"].astype(float_dtype)
        df_prices = df_prices.reset_index(drop=True).set_index(["ticker","date"])
        df_prices.sort_index(inplace=True)
        df_sms = pandas.DataFrame(columns=["date", "ticker", "positive", "tweets" ])
        for root, dirs, files in os.walk(args.sms_data_dir, topdown=True):
            for fname in sorted([x for x in files if x.endswith(".csv")]):
                fpath = os.path.realpath(os.path.join(root, fname))
                logging.info("start  cleaning {fpath}".format(fpath=fpath))
                clean_up_file(fpath)
                logging.info("finish cleaning {fpath}".format(fpath=fpath))
                logging.info("start  reading  {fpath}".format(fpath=fpath))
                df_sms_i = pandas.read_csv(fpath, skipinitialspace=True)
                try_date = date_fmt
                try:
                    datetime.strptime(str(df_sms_i["date"].head(1)[0]), try_date)
                except ValueError:
                    try_date = alt_date_fmt
                df_sms_i["date"] = pandas.to_datetime(df_sms_i["date"], format=try_date).dt.date

                logging.info("finish reading  {fpath}".format(fpath=fpath))
                logging.info("start  concat   {fpath}".format(fpath=fpath))
                df_sms = df_sms.append(df_sms_i, ignore_index=True, sort=True)
                logging.info("finish concat   {fpath}".format(fpath=fpath))
                logging.info("start  clean    dataframe")
                df_sms = clean_up_sms_df(df_sms)
                logging.info("finish clean    dataframe")
        logging.info("start  type")
        df_sms["ticker"]   = df_sms["ticker"].astype("category")
        df_sms["date"]     = pandas.to_datetime(df_sms["date"], format=date_fmt).dt.date
        df_sms["tweets"]   = df_sms["tweets"].astype(int_dtype)
        df_sms["positive"] = df_sms["positive"].astype(float_dtype)
        df_sms = df_sms.reset_index(drop=True).set_index(["ticker","date"])
        df_sms.sort_index(inplace=True)
        logging.info("finish type")
        logging.info("start  setup    db")
        if os.path.exists(out_db_path):
            os.remove(out_db_path)
        conn = sqlite3.connect(out_db_path)
        cur = conn.cursor()
        out_db_uri  = "sqlite:///{path}".format(path=out_db_path)
        disk_engine_work = create_engine(out_db_uri)
        logging.info("finish setup    db")
        logging.info("start  db       merge")
        df_merged = df_sms.merge(df_prices, how="left", on=["ticker", "date"])
        df_merged = df_merged[["tweets", "positive", "open", "close", "high", "low", "ex-dividend"]]
        count = df_merged.shape[0]
        logging.info("finish db       merge")
        logging.info("start  merge    2 db")
        df_merged.to_sql("sms_price_merge", disk_engine_work, if_exists="replace")
        logging.info("finish merge    2 db")
        print("The result database, containing {cnt} records, has been created at {dbp}".format(cnt=count, dbp=out_db_path))

    conn = sqlite3.connect(out_db_path)
    cur = conn.cursor()
    out_db_uri  = "sqlite:///{path}".format(path=out_db_path)
    disk_engine_work = create_engine(out_db_uri)
 
    if(args.dquery):
        ddate = args.dquery
        qfmt = "SELECT * FROM sms_price_merge WHERE strftime('{fmt}',date)='{ddate}'"
        df = pandas.read_sql_query(qfmt.format(ddate=ddate, fmt=date_fmt), disk_engine_work)
        with pandas.option_context("display.max_rows", None, "display.max_columns", None, "display.expand_frame_repr", False):
            print(df)

    if(args.tquery):
        tick, ddate1, ddate2 = args.tquery
        qfmt = "SELECT * FROM sms_price_merge WHERE ticker='{tick}' AND strftime('{fmt}',date)>='{ddate1}' AND strftime('{fmt}',date)<='{ddate2}';"
        df = pandas.read_sql_query(qfmt.format(tick=tick, ddate1=ddate1, ddate2=ddate2, fmt=date_fmt), disk_engine_work)
        with pandas.option_context("display.max_rows", None, "display.max_columns", None, "display.expand_frame_repr", False):
            print(df)
        df = pandas.read_sql_query("SELECT COUNT(*) FROM sms_price_merge", disk_engine_work)
        print(df)
    logging.info("end   {}".format(args))
    
def main():
    if(len(sys.argv) < 2):
        sys.argv = sys.argv + ["-h"]
    mod_conf()
    args = cli()
    run(args)

if(__name__ == "__main__"):
    main()
