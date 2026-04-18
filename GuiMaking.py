import customtkinter as ctk
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class EgxAnalyzer:

    SECTORS = [
    'Financials', 'Basic Materials', 'Industrials', 'Consumer Goods',
    'Consumer Services', 'Technology', 'Health Care', 'Utilities', 'Telecom', 'Oil & Gas']

    NAME_MAP = {
    'Abu Kir Fertilizers':                   'Abu Qir Fertilizers',
    'Alexandria Container & Cargo Handling': 'Alexandria Containers And Goods',
    'Alexandria Mineral Oils':               'Alexandria Mineral Oils Company',
    'Cairo Poultry (Koki)':                  'Cairo Poultry',
    'Commercial International Bank (CIB)':   'Commercial International Bank (Egypt)',
    'Egyptian Electrical Cables':            'Electro Cable Egypt Company',
    'El Sewedy Electric':                    'El Sewedy Electric Company',
    'Fawry':                                 'Fawry for Banking Technology and Electronic Payment',
    'Misr Capital':                          'Misr Financial Investments',
    'Orascom Construction':                  'Orascom Construction Industries',
    'Orascom Telecom Media & Technology':    'Global Telecom Holding',
    'Palm Hills Developments':               'Palm Hills Development Company',
    'Raya Holding':                          'Raya Holding for Financial Investments',
    'Talaat Moustafa Group':                 'TMG Holding',
    }
    TRADING_DAYS = 252

    def __init__(self, data='data'):
        self.df= None
        self.df2 = None
        self.sector_map = None
        self.error_message = None
        self.data = data

    def load_data(self):
        try:
            path1 = os.path.join(self.data, 'raw.csv')
            path2 = os.path.join(self.data , 'stock_data.csv')
            if not os.path.isfile(path1):
                self.error_message = f"File not found: {path1}"
                return False
            if not os.path.isfile(path2):
                self.error_message = f"File not found: {path2}"
                return False
            self.df = pd.read_csv(path1)
            self.df2 = pd.read_csv(path2)
            return True
        except Exception as e:
            self.error_message = f"Error loading data: {e}"
            return False

    def clean(self):
        try:
            # Dataset 1

            self.df.columns = self.df.columns.str.strip()
            self.df = self.df.drop(['Capital Gains', 'Dividends', 'Stock Splits'], axis=1)
            self.df['Date'] = pd.to_datetime(self.df['Date'], utc=True, errors='coerce').dt.tz_convert(None)
            self.df['Daily_Return'] = self.df.groupby('Company')['Close'].pct_change() # omar added this one

            # Dataset 2

            self.df2 = self.df2[self.df2['Sector'].isin(self.SECTORS)].copy()
            self.df2 = self.df2.dropna(subset=['Company', 'Sector']).reset_index(drop=True)

            for col in ['Price', 'M.Cap', '1D', 'YTD']:

                self.df2[col] = pd.to_numeric(
                    self.df2[col].astype(str).str.replace('%','',regex=False)
                                            .str.replace('+','',regex=False)
                                            .str.replace(',','',regex=False)
                                            .str.strip(), errors='coerce')
                                            
            # standerizering the names
            
            self.df['Company'] = self.df['Company'].replace(self.NAME_MAP)
            
            self.sector_map = (
                self.df2
                .drop_duplicates('Company')
                .set_index('Company')['Sector']
                .to_dict()
            )

            self.df['Sector'] = self.df['Company'].map(self.sector_map)

            return True
        
        except Exception as e:
            self.error_message = f"Error loading data: {e}"
            return False       
    def company_names(self):   
       
       return sorted(self.df['Company'].unique().tolist())



    def specific_company(self, company_name):
        company_data = self.df[self.df['Company'] == company_name]
        company_data2 = self.df2[self.df2['Company'] == company_name]

        if len(company_data) == 0 or len(company_data2) == 0:
            return None

        company_row = company_data2.iloc[0]

        company_data = company_data.sort_values('Date')
        latest = company_data.iloc[-1]

        annl_vol = (
            company_data['Daily_Return']
            .dropna()
            .std()
            * np.sqrt(self.TRADING_DAYS)
            * 100
        )

        company_summary = company_data[
            ['Open', 'High', 'Low', 'Close', 'Volume', 'Daily_Return']
        ].dropna().describe().to_dict()

        return {
            "company name": company_name,
            "sector": company_row['Sector'],
            "ytd": company_row['YTD'],
            "fundamental_price": company_row['Price'],
            "market_cap_fundamental": company_row['M.Cap'],

            'date_min': company_data['Date'].min(),
            'date_max': company_data['Date'].max(),

            'latest': {
                'date': latest['Date'],
                'close': float(latest['Close']),
                'volume': float(latest['Volume']),
                'market_cap': float(latest['MarketCap'])
            },

            'performance': {
                'daily_return_avg': float(company_data['Daily_Return'].mean() * 100),
                'total_gain': float(latest['Total_Gain']),
                'portfolio_value': float(latest['Portfolio_Value'])
            },

            'risk': {
                'annualized_volatility': float(annl_vol),
                'price_range_avg': float(company_data['Price_Range'].mean() * 100)
            },

            'summary_stats': company_summary
        }
    def get_volatility_data(self):
        risk = self.df.groupby('Company')['Daily_Return'].agg(
            Mean_Daily_Return='mean',
            Std_Daily_Return='std'
        ).dropna()

        risk['Ann_Return'] = risk['Mean_Daily_Return'] * self.TRADING_DAYS
        risk['Ann_Volatility'] = (
            risk['Std_Daily_Return'] * np.sqrt(self.TRADING_DAYS)
        )

        risk = risk.reset_index()
        risk['Sector'] = risk['Company'].map(self.sector_map)

        return risk.sort_values(
            'Ann_Volatility', ascending=False
        ).to_dict('records')
    
    def get_sector_growth_data(self ,invest): 
        sector_daily = self.df.groupby(
            ['Date', 'Sector']
        )['Daily_Return'].mean().reset_index()

        sector_daily = sector_daily.sort_values('Date')

        results = {}
        initial = invest

        for sector in sector_daily['Sector'].unique():

            sdata = sector_daily[
                sector_daily['Sector'] == sector
            ].copy()

            sdata['Daily_Return'] = sdata['Daily_Return'].fillna(0)

            sdata['Portfolio_Value'] = (
                initial * (1 + sdata['Daily_Return']).cumprod()
            )

            results[sector] = sdata[
                ['Date', 'Portfolio_Value']
            ].to_dict('records')

        return results

    def get_rolling_volatility_data(self, company_name, window=30):
        
        company_data = self.df[
            self.df['Company'] == company_name
        ].copy()

        if company_data.empty:
            return None

        company_data = company_data.sort_values('Date').set_index('Date')

        rolling_vol = company_data['Daily_Return'].rolling(
            window=window, min_periods=5
        ).std()

        rolling_vol_annual = (
            rolling_vol * np.sqrt(self.TRADING_DAYS) * 100
        )

        return pd.DataFrame({
            'date': rolling_vol_annual.index,
            'volatility': rolling_vol_annual.values
        }).to_dict('records')

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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

    def __init__(self ,data):
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

        print(f'Nodes: {G_sector.number_of_nodes()}')  # going to change it later
        print(f'Edges: {G_sector.number_of_edges()}')  # going to change it later

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
        plt.show()

    def PlotSector_Growth(self):
        sector_data = self.data.get_sector_growth_data(10000)
         
        fig, ax = plt.subplots(figsize=(14, 6))

        for sector,datas in sector_data.items():
            df_sector = pd.DataFrame(datas)
            ax.plot(
                pd.to_datetime(df_sector['Date']),
                df_sector['Portfolio_Value'],
                label=sector, linewidth=2
            )

        ax.set_title(
            'Growth of 10,000 EGP Investment by Sector', fontsize=14
        )
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
            dfVol['Company'], rotation=45, ha='right', fontsize=7
        )
        ax.set_title('Annualised Volatility per Company', fontsize=14, fontweight='bold')
        ax.set_xlabel('Company')
        ax.set_ylabel('Annualised Volatility (%)')

        plt.xticks(rotation=45, ha='right', fontsize=7)
        plt.tight_layout()
        plt.show()

        return fig 
    def plot_rolling_volatility(self, company_name):
        
        data = self.data.get_rolling_volatility_data(company_name)

        if not data:
            return None

        df_vol = pd.DataFrame(data)

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(
            pd.to_datetime(df_vol['date']),
            df_vol['volatility'], linewidth=2
        )
        ax.set_title(
            f'30-Day Rolling Annualised Volatility — {company_name}',
            fontsize=13, fontweight='bold'
        )
        ax.set_xlabel('Date')
        ax.set_ylabel('Rolling Volatility (%)')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        return fig

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

app = ctk.CTk()
app.geometry("1200x800")
ctk.set_appearance_mode("dark")

class FinancialData:
    def get_sector_growth_data(self):
        return {}

def clear_screen():
    for widget in app.winfo_children():
        widget.destroy()


def show_main_menu():
    clear_screen()

    label = ctk.CTkLabel(master=app, text="EGX Stocks",width=300, height=60, font=("Arial", 24), text_color="#FFCC70")
    label.place(relx=0.5, rely=0.2, anchor="center")

    scrapingBTN = ctk.CTkButton(master=app, text="Scraping",width=300, height=60, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_scraping_page)
    scrapingBTN.place(relx=0.2, rely=0.5, anchor="center")

    LDataBTN = ctk.CTkButton(master=app, text="Loading Data and Cleaning",width=300, height=60, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_Ldata_page)
    LDataBTN.place(relx=0.5, rely=0.5, anchor="center")

    compBTN = ctk.CTkButton(master=app, text="Specific company for analysis",width=300, height=60, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_comp_page)
    compBTN.place(relx=0.8, rely=0.5, anchor="center")

    networkBTN = ctk.CTkButton(master=app, text="Network",width=300, height=60, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_network_page)
    networkBTN.place(relx=0.2, rely=0.7, anchor="center")

    pltsectorBTN = ctk.CTkButton(master=app, text="Plot Sector Growth",width=300, height=60, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_pltsector_page)
    pltsectorBTN.place(relx=0.5, rely=0.7, anchor="center")

    volBTN = ctk.CTkButton(master=app, text="Volatility",width=300, height=60, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_vol_page)
    volBTN.place(relx=0.8, rely=0.7, anchor="center")

def show_network_page():
    for widget in app.winfo_children():
        widget.destroy()

    new_label = ctk.CTkLabel(master=app, text="NetworkX Analysis", font=("Arial", 24))
    new_label.place(relx=0.5, rely=0.3, anchor="center")

    backBTN = ctk.CTkButton(master=app, text="Go Back",width=200, height=50, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_main_menu)
    backBTN.place(relx=0.1, rely=0.95, anchor="center")

def show_scraping_page():
    for widget in app.winfo_children():
        widget.destroy()

    new_label = new_label = ctk.CTkLabel(master=app, text="Scraping", font=("Arial", 24))
    new_label.place(relx=0.5, rely=0.3, anchor="center")

    backBTN = ctk.CTkButton(master=app, text="Go Back",width=200, height=50, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_main_menu)
    backBTN.place(relx=0.1, rely=0.95, anchor="center")

def show_Ldata_page():
    for widget in app.winfo_children():
        widget.destroy()

    new_label = ctk.CTkLabel(master=app, text="Loading Data and Cleaning", font=("Arial", 24))
    new_label.place(relx=0.5, rely=0.3, anchor="center")

    backBTN = ctk.CTkButton(master=app, text="Go Back",width=200, height=50, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_main_menu)
    backBTN.place(relx=0.1, rely=0.95, anchor="center")

def show_comp_page():
    for widget in app.winfo_children():
        widget.destroy()

    new_label = ctk.CTkLabel(master=app, text="Specific company for analysis", font=("Arial", 24))
    new_label.place(relx=0.5, rely=0.3, anchor="center")

    backBTN = ctk.CTkButton(master=app, text="Go Back",width=200, height=50, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_main_menu)
    backBTN.place(relx=0.1, rely=0.95, anchor="center")


def show_pltsector_page():
    for widget in app.winfo_children():
        widget.destroy()

    new_label = ctk.CTkLabel(master=app, text="Plot Sector Growth", font=("Arial", 24))
    new_label.place(relx=0.5, rely=0.05, anchor="center")

    fig = analyzer.PlotSector_Growth() 

    canvas = FigureCanvasTkAgg(fig, master=app)  
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.place(relx=0.5, rely=0.5, anchor="center")

    backBTN = ctk.CTkButton(master=app, text="Go Back",width=200, height=50, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_main_menu)
    backBTN.place(relx=0.1, rely=0.95, anchor="center")

def show_vol_page():
    for widget in app.winfo_children():
        widget.destroy()
        
    new_label = ctk.CTkLabel(master=app, text="Volatility", font=("Arial", 24))
    new_label.place(relx=0.5, rely=0.3, anchor="center")

    backBTN = ctk.CTkButton(master=app, text="Go Back",width=200, height=50, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_main_menu)
    backBTN.place(relx=0.1, rely=0.95, anchor="center")


data_engine = EgxAnalyzer(data='data')

if data_engine.load_data():
    data_engine.clean()
    analyzer = EgxVisualization(data=data_engine)
else:
    print(data_engine.error_message)



show_main_menu()
app.mainloop()