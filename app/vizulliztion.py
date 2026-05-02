import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
import pandas as pd
import numpy as np

class EgxVisualization:

    sector_colors = {
        'Financials':        '#e74c3c',
        'Basic Materials':   "#4a2525",
        'Industrials':       '#2ecc71',
        'Consumer Goods':    '#f39c12',
        'Consumer Services': '#9b59b6',
        'Technology':        '#1abc9c',
        'Health Care':       '#e91e63',
        'Utilities':         '#00bcd4',
        'Telecom':           "#3122ff",
        'Oil & Gas':         "#080808"
    }

    def __init__(self, data):
        self.data = data    
        

    def networkx_sector(self):

        G_sector = nx.Graph()

        grouped = self.data.df.groupby('Sector')

        for sector, group in grouped:

            companies = group['Company'].dropna().unique()

            for company in companies:
                G_sector.add_node(company, sector=sector)

            for i in range(len(companies)):
                for j in range(i + 1, len(companies)):
                    G_sector.add_edge(companies[i], companies[j])

        node_colors = [
            self.sector_colors.get(
                G_sector.nodes[n].get('sector', ''),
                '#95a5a6'
            )
            for n in G_sector.nodes()
        ]

        fig, ax = plt.subplots(figsize=(14, 10))

        pos = nx.spring_layout(G_sector, k=2, iterations=50, seed=42)

        nx.draw_networkx_nodes(
            G_sector, pos, ax=ax,
            node_color=node_colors,
            node_size=800,
            alpha=0.9
        )

        nx.draw_networkx_edges(
            G_sector, pos, ax=ax,
            edge_color='#000000',
            width=0.5,
            alpha=0.3
        )

        nx.draw_networkx_labels(
            G_sector, pos, ax=ax,
            font_size=7,
            font_weight='bold'
        )

        legend_list = [
            plt.Line2D(
                [0], [0],
                marker='o',
                color='w',
                markerfacecolor=c,
                markersize=10,
                label=s
            )
            for s, c in self.sector_colors.items()
            if s in self.data.df['Sector'].dropna().unique()
        ]

        ax.legend(handles=legend_list, loc='upper left', fontsize=9)

        ax.set_title('EGX Companies Network — Grouped by Sector', fontsize=14)
        ax.axis('off')

        plt.tight_layout()
        return fig

    def PlotSector_Growth(self):

        sector_data = self.data.get_sector_growth_data()

        fig, ax = plt.subplots(figsize=(14, 6))

        for sector, datas in sector_data.items():

            df_sector = pd.DataFrame(datas)

            ax.plot(
                pd.to_datetime(df_sector['Date']),
                df_sector['Portfolio_Value'],
                label=sector, linewidth=2
            )

        ax.set_title('Growth of 10,000 EGP Investment by Sector', fontsize=14)
        ax.set_xlabel('Date')
        ax.set_ylabel('Portfolio Value (EGP)')
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def PlotVolatility(self):

        vol_data = self.data.get_volatility_data()
        dfVol = pd.DataFrame(vol_data)

        fig, ax = plt.subplots(figsize=(13, 6))

        ax.bar(range(len(dfVol)), dfVol['Ann_Volatility'])
        ax.set_xticks(range(len(dfVol)))

        ax.set_xticklabels(
            dfVol['Company'],
            rotation=45,
            ha='right',
            fontsize=7
        )

        ax.set_title('Annualised Volatility per Company', fontsize=14)
        ax.set_xlabel('Company')
        ax.set_ylabel('Annualised Volatility (%)')

        plt.tight_layout()
        return fig

    def plot_rolling_volatility(self, company_name):

        data = self.data.get_rolling_volatility_data(company_name)

        if not data:
            return None

        df_vol = pd.DataFrame(data)

        fig, ax = plt.subplots(figsize=(14, 5))

        ax.plot(
            pd.to_datetime(df_vol['date']),
            df_vol['volatility'],
            linewidth=2
        )

        ax.set_title(
            f'30-Day Rolling Annualised Volatility — {company_name}',
            fontsize=13
        )

        ax.set_xlabel('Date')
        ax.set_ylabel('Volatility (%)')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig
    
    def heatmap(self, companies, monthly_perf):

        recent_12_months = sorted(monthly_perf["Month"].unique())[-12:]

        plot_df = monthly_perf[
            (monthly_perf["Company"].isin(companies)) &
            (monthly_perf["Month"].isin(recent_12_months))
        ].pivot(
            index="Company",
            columns="Month",
            values="Monthly_Return"
        )

        # 4. Create the Plot
        fig ,ax  = plt.subplots(figsize=(14, 10))
        sns.heatmap(plot_df.astype(float), annot=True, fmt=".2f", cmap='RdYlGn', center=0,
                    linewidths=.5, cbar_kws={'label': 'Monthly Return %'})

        ax.set_title("EGX Monthly Performance: Top Companies", fontsize=16)
        ax.set_ylabel("Company")
        ax.set_xlabel("Month")

        plt.tight_layout()

        return fig
        

    def plot_gainers(self, n=5):

        monthly_perf = self.data.get_monthly()
        x = self.data.top_n_per_month(monthly_perf, n)

        latest = x[x["Month"] == x["Month"].max()]
        data = latest[latest["Type"] == "Gainer"].sort_values(
            "Monthly_Return",
            ascending=False
        )

        fig, ax = plt.subplots(figsize=(7, 5))

        ax.barh(data["Company"], data["Monthly_Return"], color="#2ecc71")
        ax.set_title(f"Top {n} Gainers")
        ax.axvline(0, color="black", linewidth=0.8)
        ax.invert_yaxis()

        plt.tight_layout()
        return fig
    
    def plot_losers(self, n=5):

        monthly_perf = self.data.get_monthly()
        x = self.data.top_n_per_month(monthly_perf, n)

        latest = x[x["Month"] == x["Month"].max()]
        data = latest[latest["Type"] == "Loser"].sort_values(
            "Monthly_Return",
            ascending=True
        )

        fig, ax = plt.subplots(figsize=(7, 5))

        ax.barh(data["Company"], data["Monthly_Return"], color="#e74c3c")
        ax.set_title(f"Top {n} Losers")
        ax.axvline(0, color="black", linewidth=0.8)
        ax.invert_yaxis()

        plt.tight_layout()
        return fig

        