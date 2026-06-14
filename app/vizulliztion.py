import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
import pandas as pd
import plotly.express as px

from core.metrics import company_monthly_returns, monthly_performance, rolling_volatility, top_n_per_month, three_d_monthly_data
from core.sector import sector_growth_data


class EgxVisualization:

    sector_colors = {
        "Financials": "#e74c3c",
        "Basic Materials": "#4a2525",
        "Industrials": "#2ecc71",
        "Consumer Goods": "#f39c12",
        "Consumer Services": "#9b59b6",
        "Technology": "#1abc9c",
        "Health Care": "#e91e63",
        "Utilities": "#00bcd4",
        "Telecom": "#3122ff",
        "Oil & Gas": "#080808",
    }

    def __init__(self, data):
        self.data = data

    def _empty_fig(self, title):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_title(title)
        ax.axis("off")
        return fig

    def plot_company_price(self, company_name):
        company_df = self.data.company_frame(company_name)
        if company_df.empty:
            return self._empty_fig(f"Price Trend - {company_name}")

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(pd.to_datetime(company_df["Date"]), company_df["Close"], linewidth=2)
        ax.set_title(f"Price Trend - {company_name}", fontsize=13)
        ax.set_xlabel("Date")
        ax.set_ylabel("Close")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_company_monthly_returns(self, company_name):
        monthly = company_monthly_returns(self.data.df, company_name)
        if monthly.empty:
            return self._empty_fig(f"Monthly Returns - {company_name}")

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.bar(monthly["Month"], monthly["Monthly_Return"])
        ax.set_title("Monthly Returns", fontsize=13)
        ax.set_xlabel("Month")
        ax.set_ylabel("Return %")
        ax.tick_params(axis="x", rotation=45)
        plt.tight_layout()
        return fig

    def networkx_sector(self):
        graph = nx.Graph()
        grouped = self.data.df.groupby("Sector")

        for sector, group in grouped:
            companies = group["Company"].dropna().unique()
            for company in companies:
                graph.add_node(company, sector=sector)
            for i in range(len(companies)):
                for j in range(i + 1, len(companies)):
                    graph.add_edge(companies[i], companies[j])

        node_colors = [
            self.sector_colors.get(graph.nodes[n].get("sector", ""), "#95a5a6")
            for n in graph.nodes()
        ]

        fig, ax = plt.subplots(figsize=(14, 10))
        pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)

        nx.draw_networkx_nodes(graph, pos, ax=ax, node_color=node_colors, node_size=800, alpha=0.9)
        nx.draw_networkx_edges(graph, pos, ax=ax, edge_color="#000000", width=0.5, alpha=0.3)
        nx.draw_networkx_labels(graph, pos, ax=ax, font_size=7, font_weight="bold")

        legend_list = [
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=10, label=s)
            for s, c in self.sector_colors.items()
            if s in self.data.df["Sector"].dropna().unique()
        ]

        ax.legend(handles=legend_list, loc="upper left", fontsize=9)
        ax.set_title("EGX Companies Network — Grouped by Sector", fontsize=14)
        ax.axis("off")
        plt.tight_layout()
        return fig

    def PlotSector_Growth(self):
        sector_data = sector_growth_data(self.data.df)
        fig, ax = plt.subplots(figsize=(14, 6))

        for sector, records in sector_data.items():
            df_sector = pd.DataFrame(records)
            ax.plot(pd.to_datetime(df_sector["Date"]), df_sector["Portfolio_Value"], label=sector, linewidth=2)

        ax.set_title("Growth of 10,000 EGP Investment by Sector", fontsize=14)
        ax.set_xlabel("Date")
        ax.set_ylabel("Portfolio Value (EGP)")
        ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def PlotVolatility(self):
        vol_data = self.data.get_volatility_data()
        df_vol = pd.DataFrame(vol_data)

        if df_vol.empty:
            return self._empty_fig("Annualised Volatility per Company")

        fig, ax = plt.subplots(figsize=(13, 6))
        ax.bar(range(len(df_vol)), df_vol["Ann_Volatility"])
        ax.set_xticks(range(len(df_vol)))
        ax.set_xticklabels(df_vol["Company"], rotation=45, ha="right", fontsize=7)
        ax.set_title("Annualised Volatility per Company", fontsize=14)
        ax.set_xlabel("Company")
        ax.set_ylabel("Annualised Volatility (%)")
        plt.tight_layout()
        return fig

    def plot_rolling_volatility(self, company_name):
        data = rolling_volatility(self.data.df, company_name)
        if data.empty:
            return self._empty_fig(f"30-Day Rolling Annualised Volatility — {company_name}")

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(pd.to_datetime(data["date"]), data["volatility"], linewidth=2)
        ax.set_title(f"30-Day Rolling Annualised Volatility — {company_name}", fontsize=13)
        ax.set_xlabel("Date")
        ax.set_ylabel("Volatility (%)")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def heatmap(self, companies, monthly_perf):
        if monthly_perf is None or monthly_perf.empty or not companies:
            return self._empty_fig("EGX Monthly Performance: Top Companies")

        recent_12_months = sorted(monthly_perf["Month"].unique())[-12:]

        plot_df = monthly_perf[
            (monthly_perf["Company"].isin(companies)) &
            (monthly_perf["Month"].isin(recent_12_months))
        ].pivot(
            index="Company",
            columns="Month",
            values="Monthly_Return",
        )

        fig, ax = plt.subplots(figsize=(14, 10))
        sns.heatmap(
            plot_df.astype(float),
            annot=True,
            fmt=".2f",
            cmap="RdYlGn",
            center=0,
            linewidths=.5,
            cbar_kws={"label": "Monthly Return %"},
            ax=ax,
        )

        ax.set_title("EGX Monthly Performance: Top Companies", fontsize=16)
        ax.set_ylabel("Company")
        ax.set_xlabel("Month")
        plt.tight_layout()
        return fig

    def plot_gainers(self, n=5):
        monthly_perf = monthly_performance(self.data.df)
        x = top_n_per_month(monthly_perf, n)

        if x.empty:
            return self._empty_fig(f"Top {n} Gainers")

        latest = x[x["Month"] == x["Month"].max()]
        data = latest[latest["Type"] == "Gainer"].sort_values("Monthly_Return", ascending=False)

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.barh(data["Company"], data["Monthly_Return"], color="#2ecc71")
        ax.set_title(f"Top {n} Gainers")
        ax.axvline(0, color="black", linewidth=0.8)
        ax.invert_yaxis()
        plt.tight_layout()
        return fig

    def plot_losers(self, n=5):
        monthly_perf = monthly_performance(self.data.df)
        x = top_n_per_month(monthly_perf, n)

        if x.empty:
            return self._empty_fig(f"Top {n} Losers")

        latest = x[x["Month"] == x["Month"].max()]
        data = latest[latest["Type"] == "Loser"].sort_values("Monthly_Return", ascending=True)

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.barh(data["Company"], data["Monthly_Return"], color="#e74c3c")
        ax.set_title(f"Top {n} Losers")
        ax.axvline(0, color="black", linewidth=0.8)
        ax.invert_yaxis()
        plt.tight_layout()
        return fig

    def ThreeD_plt(self):
        plot_df = three_d_monthly_data(self.data.df).copy()

        if plot_df.empty:
            return px.scatter_3d()

        vol_limit = plot_df["Monthly_Volatility"].median()
        volume_limit = plot_df["Monthly_Volume"].median()

        plot_df["Status"] = "RED"
        plot_df.loc[
            (plot_df["Monthly_Return"] > 0) &
            (plot_df["Monthly_Volatility"] <= vol_limit) &
            (plot_df["Monthly_Volume"] >= volume_limit),
            "Status"
        ] = "GREEN"

        plot_df.loc[
            (plot_df["Status"] != "GREEN") &
            (
                (plot_df["Monthly_Return"] > 0) |
                (plot_df["Monthly_Volume"] >= volume_limit)
            ),
            "Status"
        ] = "ORANGE"

        fig = px.scatter_3d(
            plot_df,
            x="Monthly_Return",
            y="Monthly_Volatility",
            z="Monthly_Volume",
            color="Status",
            hover_name="Company",
            hover_data=["Month", "Monthly_Return", "Monthly_Volatility", "Monthly_Volume"],
            title="EGX Monthly Returns, Volatility and Volume (3D View)",
            color_discrete_map={
                "GREEN": "#2ecc71",
                "ORANGE": "#f39c12",
                "RED": "#e74c3c",
            },
        )

        fig.update_layout(
            legend_title_text="Status",
            scene=dict(
                xaxis_title="Monthly Return",
                yaxis_title="Monthly Volatility",
                zaxis_title="Monthly Volume",
            ),
        )

        return fig
