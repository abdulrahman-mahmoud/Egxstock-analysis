import customtkinter as ctk
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

from analyzer import EgxAnalyzer
from scraper import EgxScraper
from vizulliztion import EgxVisualization


app = ctk.CTk()
app.geometry("1200x800")
ctk.set_appearance_mode("dark")


data_engine = EgxAnalyzer(data='data')

viz_engine = None

if data_engine.load_data():
    data_engine.clean()
    viz_engine = EgxVisualization(data_engine)
else:
    print(data_engine.error_message)


def clear_screen():
    for widget in app.winfo_children():
        widget.destroy()


def show_main_menu():
    clear_screen()

    label = ctk.CTkLabel(
        master=app,
        text="EGX Stocks",
        width=300,
        height=60,
        font=("Arial", 24),
        text_color="#FFCC70"
    )
    label.place(relx=0.5, rely=0.2, anchor="center")

    ctk.CTkButton(app, text="Scraping",
                  command=show_scraping_page).place(relx=0.2, rely=0.5, anchor="center")

    ctk.CTkButton(app, text="Loading Data and Cleaning",
                  command=show_Ldata_page).place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkButton(app, text="Specific company for analysis",
                  command=show_comp_page).place(relx=0.8, rely=0.5, anchor="center")

    ctk.CTkButton(app, text="Network",
                  command=show_network_page).place(relx=0.2, rely=0.7, anchor="center")

    ctk.CTkButton(app, text="Plot Sector Growth",
                  command=show_pltsector_page).place(relx=0.5, rely=0.7, anchor="center")

    ctk.CTkButton(app, text="Volatility",
                  command=show_vol_page).place(relx=0.8, rely=0.7, anchor="center")


# -----------------------------------------------------------------
# PAGES
# -----------------------------------------------------------------
def show_network_page():
    clear_screen()

    ctk.CTkLabel(app, text="NetworkX Analysis",
                 font=("Arial", 24)).place(relx=0.5, rely=0.3, anchor="center")

    viz_engine.networkx_sector()

    ctk.CTkButton(app, text="Go Back",
                  command=show_main_menu).place(relx=0.1, rely=0.95)


def show_scraping_page():
    clear_screen()

    ctk.CTkLabel(app, text="Scraping",
                 font=("Arial", 24)).place(relx=0.5, rely=0.3, anchor="center")

    ctk.CTkButton(app, text="Go Back",
                  command=show_main_menu).place(relx=0.1, rely=0.95)


def show_Ldata_page():
    clear_screen()

    ctk.CTkLabel(app, text="Loading Data and Cleaning",
                 font=("Arial", 24)).place(relx=0.5, rely=0.3, anchor="center")

    ctk.CTkButton(app, text="Go Back",
                  command=show_main_menu).place(relx=0.1, rely=0.95)


def show_comp_page():
    clear_screen()

    ctk.CTkLabel(app, text="Specific company for analysis",
                 font=("Arial", 24)).place(relx=0.5, rely=0.3, anchor="center")

    ctk.CTkButton(app, text="Go Back",
                  command=show_main_menu).place(relx=0.1, rely=0.95)


def show_pltsector_page():
    clear_screen()

    ctk.CTkLabel(app, text="Plot Sector Growth",
                 font=("Arial", 24)).place(relx=0.5, rely=0.05, anchor="center")

    fig = viz_engine.PlotSector_Growth()

    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    canvas.get_tk_widget().place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkButton(app, text="Go Back",
                  command=show_main_menu).place(relx=0.1, rely=0.95)


def show_vol_page():
    clear_screen()

    ctk.CTkLabel(app, text="Volatility",
                 font=("Arial", 24)).place(relx=0.5, rely=0.3, anchor="center")

    fig = viz_engine.PlotVolatility()

    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    canvas.get_tk_widget().place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkButton(app, text="Go Back",
                  command=show_main_menu).place(relx=0.1, rely=0.95)


# -----------------------------------------------------------------
# RUN APP
# -----------------------------------------------------------------
show_main_menu()
app.mainloop()