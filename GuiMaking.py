import customtkinter as ctk
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np

app = ctk.CTk()
app.geometry("1200x800")
ctk.set_appearance_mode("dark")

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
    new_label.place(relx=0.5, rely=0.3, anchor="center")

    backBTN = ctk.CTkButton(master=app, text="Go Back",width=200, height=50, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_main_menu)
    backBTN.place(relx=0.1, rely=0.95, anchor="center")

def show_vol_page():
    for widget in app.winfo_children():
        widget.destroy()

    new_label = ctk.CTkLabel(master=app, text="Volatility", font=("Arial", 24))
    new_label.place(relx=0.5, rely=0.3, anchor="center")

    backBTN = ctk.CTkButton(master=app, text="Go Back",width=200, height=50, corner_radius=16, fg_color="#EFBF04", hover_color="#A57C00", border_color="#D4AF37", border_width=2, command=show_main_menu)
    backBTN.place(relx=0.1, rely=0.95, anchor="center")



show_main_menu()
app.mainloop()