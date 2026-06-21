import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.metrics import company_monthly_returns, monthly_performance, rolling_volatility, top_n_per_month, three_d_monthly_data
from app.sector import sector_growth_data


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
        "Real Estate": "#8e44ad",
        "Banking": "#2980b9",
        "FinTech": "#16a085",
        "Automotive": "#d35400",
        "ETF": "#7f8c8d",
    }

    def __init__(self, data):
        self.data = data

    def _empty_fig(self, title):
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16),
        )
        fig.update_layout(
            title=title,
            template="plotly_white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400,
        )
        return fig

    def plot_company_price(self, company_name):
        company_df = self.data.company_frame(company_name)
        if company_df.empty:
            return self._empty_fig(f"Price Trend - {company_name}")

        fig = px.line(
            company_df,
            x=pd.to_datetime(company_df["Date"]),
            y="Close",
            title=f"Price Trend - {company_name}",
            template="plotly_white",
        )
        fig.update_traces(line=dict(width=3))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Close",
            height=450,
        )
        return fig

    def plot_company_monthly_returns(self, company_name):
        monthly = company_monthly_returns(self.data.df, company_name)
        if monthly.empty:
            return self._empty_fig(f"Monthly Returns - {company_name}")

        fig = px.bar(
            monthly,
            x="Month",
            y="Monthly_Return",
            title=f"Monthly Returns - {company_name}",
            template="plotly_white",
        )
        fig.update_traces(marker_color="#3498db")
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Return %",
            height=450,
        )
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

        if graph.number_of_nodes() == 0:
            return self._empty_fig("EGX Companies Network - Grouped by Sector")

        pos = nx.spring_layout(
            graph,
            k=1 / max(len(graph.nodes()) ** 0.5, 1),
            iterations=100,
            seed=42,
        )

        edge_x = []
        edge_y = []
        for source, target in graph.edges():
            x0, y0 = pos[source]
            x1, y1 = pos[target]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=0.5, color="rgba(0,0,0,0.25)"),
            hoverinfo="none",
            mode="lines",
        )

        traces = [edge_trace]
        seen_sectors = []
        for node, attrs in graph.nodes(data=True):
            sector = attrs.get("sector", "")
            if sector not in seen_sectors:
                seen_sectors.append(sector)

        for sector in seen_sectors:
            sector_nodes = [node for node, attrs in graph.nodes(data=True) if attrs.get("sector", "") == sector]
            traces.append(
                go.Scatter(
                    x=[pos[node][0] for node in sector_nodes],
                    y=[pos[node][1] for node in sector_nodes],
                    mode="markers+text",
                    text=sector_nodes,
                    textposition="top center",
                    textfont=dict(size=10),
                    name=sector or "Unknown",
                    hovertext=[f"{node}<br>Sector: {sector or 'Unknown'}" for node in sector_nodes],
                    hoverinfo="text",
                    marker=dict(
                        size=18,
                        color=self.sector_colors.get(sector, "#95a5a6"),
                        line=dict(width=1, color="#ffffff"),
                        opacity=0.95,
                    ),
                )
            )

        fig = go.Figure(data=traces)
        fig.update_layout(
            title="EGX Companies Network - Grouped by Sector",
            template="plotly_white",
            showlegend=True,
            legend_title_text="Sector",
            hovermode="closest",
            height=800,
            margin=dict(l=20, r=20, t=60, b=20),
        )
        fig.update_xaxes(visible=False, showgrid=False, zeroline=False)
        fig.update_yaxes(visible=False, showgrid=False, zeroline=False)
        return fig

    def PlotSector_Growth(self):
        sector_data = sector_growth_data(self.data.df)
        frames = []
        for sector, records in sector_data.items():
            df_sector = pd.DataFrame(records)
            if not df_sector.empty:
                df_sector = df_sector.copy()
                df_sector["Date"] = pd.to_datetime(df_sector["Date"])
                df_sector["Sector"] = sector
                frames.append(df_sector)

        if not frames:
            return self._empty_fig("Growth of 10,000 EGP Investment by Sector")

        plot_df = pd.concat(frames, ignore_index=True)
        fig = px.line(
            plot_df,
            x="Date",
            y="Portfolio_Value",
            color="Sector",
            title="Growth of 10,000 EGP Investment by Sector",
            template="plotly_white",
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Portfolio Value (EGP)",
            height=500,
            legend_title_text="Sector",
        )
        return fig

    def PlotVolatility(self):
        vol_data = self.data.get_volatility_data()
        df_vol = pd.DataFrame(vol_data)

        if df_vol.empty:
            return self._empty_fig("Annualised Volatility per Company")

        fig = px.bar(
            df_vol,
            x="Company",
            y="Ann_Volatility",
            title="Annualised Volatility per Company",
            template="plotly_white",
        )
        fig.update_traces(marker_color="#8e44ad")
        fig.update_layout(
            xaxis_title="Company",
            yaxis_title="Annualised Volatility (%)",
            height=500,
            xaxis_tickangle=-45,
        )
        return fig

    def plot_rolling_volatility(self, company_name):
        data = rolling_volatility(self.data.df, company_name)
        if data.empty:
            return self._empty_fig(f"30-Day Rolling Annualised Volatility — {company_name}")

        fig = px.line(
            data,
            x=pd.to_datetime(data["date"]),
            y="volatility",
            title=f"30-Day Rolling Annualised Volatility - {company_name}",
            template="plotly_white",
        )
        fig.update_traces(line=dict(width=3, color="#16a085"))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Volatility (%)",
            height=450,
        )
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

        fig = go.Figure(
            data=go.Heatmap(
                z=plot_df.astype(float).values,
                x=plot_df.columns.tolist(),
                y=plot_df.index.tolist(),
                colorscale="RdYlGn",
                zmid=0,
                colorbar=dict(title="Monthly Return %"),
                hovertemplate="Company=%{y}<br>Month=%{x}<br>Return=%{z:.2f}%<extra></extra>",
            )
        )
        fig.update_layout(
            title="EGX Monthly Performance: Top Companies",
            template="plotly_white",
            xaxis_title="Month",
            yaxis_title="Company",
            height=700,
        )
        return fig

    def plot_gainers(self, n=5):
        monthly_perf = monthly_performance(self.data.df)
        x = top_n_per_month(monthly_perf, n)

        if x.empty:
            return self._empty_fig(f"Top {n} Gainers")

        latest = x[x["Month"] == x["Month"].max()]
        data = latest[latest["Type"] == "Gainer"].sort_values("Monthly_Return", ascending=False)

        fig = px.bar(
            data.sort_values("Monthly_Return", ascending=True),
            x="Monthly_Return",
            y="Company",
            orientation="h",
            title=f"Top {n} Gainers",
            template="plotly_white",
        )
        fig.update_traces(marker_color="#2ecc71")
        fig.update_layout(
            xaxis_title="Monthly Return %",
            yaxis_title="Company",
            height=450,
        )
        return fig

    def plot_losers(self, n=5):
        monthly_perf = monthly_performance(self.data.df)
        x = top_n_per_month(monthly_perf, n)

        if x.empty:
            return self._empty_fig(f"Top {n} Losers")

        latest = x[x["Month"] == x["Month"].max()]
        data = latest[latest["Type"] == "Loser"].sort_values("Monthly_Return", ascending=True)

        fig = px.bar(
            data,
            x="Monthly_Return",
            y="Company",
            orientation="h",
            title=f"Top {n} Losers",
            template="plotly_white",
        )
        fig.update_traces(marker_color="#e74c3c")
        fig.update_layout(
            xaxis_title="Monthly Return %",
            yaxis_title="Company",
            height=450,
        )
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
