from dataclasses import dataclass
from loguru import logger
import numpy as np
import yfinance as yf
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt

yf.pdr_override()


@dataclass
class StrategySimulator:
    symbol: str
    start_date: str
    end_date: str
    day_of_week_to_invest: int
    day_of_month_to_invest: int

    def __post_init__(self):
        self.check_days_validity()

    def check_days_validity(self):
        if self.day_of_week_to_invest not in np.arange(stop=7):
            logger.error(
                f"{self.day_of_week_to_invest} is not a valid day of week. Please provide one between 0 (Monday) and 6 (Sunday) included."
            )

        elif self.day_of_month_to_invest not in np.arange(start=1, stop=32):
            logger.error(
                f"{self.day_of_month_to_invest} is not a valid day of month. Please provide one between 1 and 31."
            )
        else:
            return

    def get_df(self):
        df = pdr.get_data_yahoo(self.symbol, start=self.start_date, end=self.end_date)
        df["day_of_week"] = df.index.day_of_week
        df["day_of_month"] = df.index.day

        df["weekly_investment"] = 0
        df.loc[df["day_of_week"] == self.day_of_week_to_invest, "weekly_investment"] = 1
        df["monthly_investment"] = 0
        df.loc[
            df["day_of_month"] == self.day_of_month_to_invest, "monthly_investment"
        ] = 1

        df["weekly_shares"] = df["weekly_investment"] / df["High"]
        df["monthly_shares"] = df["monthly_investment"] / df["High"]

        self.plot_highest_price(df)
        return df

    def plot_highest_price(self, df):
        plt.plot(df.index, df["High"])
        plt.xlabel("Time")
        plt.ylabel("Highest price of the day [€]")

    def get_number_of_traded_days(self, df):
        traded_days_weekly = sum(df["weekly_investment"])
        traded_days_monthly = sum(df["monthly_investment"])
        logger.info(
            f"Days invested with the weekly strategy = {traded_days_weekly} \nDays invested with the monthly strategy = {traded_days_monthly}"
        )
        return traded_days_weekly, traded_days_monthly

    def get_shares_per_traded_day(self, df):
        traded_days_weekly, traded_days_monthly = self.get_number_of_traded_days(df)
        shares_per_traded_day_weekly = sum(df["weekly_shares"]) / traded_days_weekly
        shares_per_traded_day_monthly = sum(df["monthly_shares"]) / traded_days_monthly
        logger.info(
            f"Shares per traded day with weekly strategy = {shares_per_traded_day_weekly} \nShares per traded day with monthly strategy = {shares_per_traded_day_monthly}"
        )
        return shares_per_traded_day_weekly, shares_per_traded_day_monthly

    def compute_what_is_best_strategy(self, df):
        shares_per_traded_day_weekly, shares_per_traded_day_monthly = (
            self.get_shares_per_traded_day(df)
        )
        ratio_weekly_monthly = (
            shares_per_traded_day_weekly / shares_per_traded_day_monthly
        )
        percent_weekly_over_monthly = (ratio_weekly_monthly - 1) * 100

        logger.info(
            f"On average, trading weekly instead of monthly was {percent_weekly_over_monthly}% better."
        )

        final_price = df.iloc[-1]["Close"]
        gain_per_share_weekly = shares_per_traded_day_weekly * final_price
        gain_per_share_monthly = shares_per_traded_day_monthly * final_price

        logger.info(
            f"For each € invested weekly, from {self.start_date} to {self.end_date}, one would earn {gain_per_share_weekly} by selling on the {df.index[-1]}"
        )
        logger.info(
            f"For each € invested monthly, from {self.start_date} to {self.end_date}, one would earn {gain_per_share_monthly} by selling on the {df.index[-1]}"
        )
