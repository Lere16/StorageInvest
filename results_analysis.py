import os

import pandas as pd
import numpy as np
from matplotlib import rcParams
from matplotlib import pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = 'firefox'
from plotly.offline import plot
import os
import altair as alt
from datetime import datetime, timedelta
from altair_saver import save
from matplotlib.colors import to_hex
import plotly.express as px
import plotly.figure_factory as ff
import seaborn as sns
import statsmodels.api as sm
import plotly.graph_objects as go
#from matplotlib.ticker import ScalarFormatter
from matplotlib.ticker import FuncFormatter





def plotdataAnalysis(load_df, price_df):
    
    output_dir_plot = 'results/plots/data_analysis'
    os.makedirs(output_dir_plot, exist_ok=True)
    
    #1. HISTOGRAM OF ELECTRICITY PRICES
    histogram_plot(price_df, output_dir_plot)
    
    #2. AVERAGE ELECTRICITY PRICE 
    average_price_plot(price_df, output_dir_plot)
    
    
    #3. HEATMAP OF ELECTRICITY PRICES
    heatmap_plot(price_df, output_dir_plot)    
    heatmap_plot_2(price_df, output_dir_plot)
    
    #3. HEATMAP OF ELECTRICITY PRICE FOR EACH MONTH
    heatmap_month_plot(price_df, output_dir_plot)
        
    # HEATMAP 2
    heatmap_month_plot_2(price_df, output_dir_plot)
    
    # HEATMAP 3
    heatmap_month_plot_3(price_df, output_dir_plot)
    
    # HEATMAP VOLATILITY
    volatility_heatmap(price_df, output_dir_plot)
    
    # ROLLING VOLATILITY
    rolling_volatility_plot(price_df, output_dir_plot)
    
    # BOX PLOT
    boxplot_prices(price_df, output_dir_plot)
    
    
    return None 

def histogram_plot(price_df, output_dir_plot):
    sns.set(style="whitegrid")
    # Création de l'histogramme
    plt.figure(figsize=(7, 5))
    sns.histplot(price_df['Day-ahead Price [EUR/MWh]'], bins=70, kde=True, color='blue')
    # Ajout de titres et d'étiquettes
    #plt.title('Distribution des prix horaires de l\'électricité\n(Bidding Zone Allemagne)', fontsize=16)
    plt.xlabel('Electricity price [EUR/MWh]', fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    # Formatage des ticks pour qu'ils soient plus lisibles
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    # Affichage de la figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "price_distribution.png"), dpi=400)
    
    return None

def average_price_plot(price_df, output_dir_plot ):
    df1=price_df.copy()
    df1['Time'] = pd.to_datetime(df1['Time'], format='%d/%m/%Y %H:%M')
    # Extraction des colonnes pour les années, mois et jours
    df1['Year'] = df1['Time'].dt.year
    df1['Month'] = df1['Time'].dt.month
    df1['Day'] = df1['Time'].dt.day
    # Calcul des prix moyens mensuels
    monthly_avg = df1.groupby(['Year', 'Month'])['Day-ahead Price [EUR/MWh]'].mean().reset_index()
    # Création d'une colonne 'Month-Year' pour l'affichage
    monthly_avg['Month-Year'] = monthly_avg['Year'].astype(str) + '-' + monthly_avg['Month'].astype(str)
    # Configuration de style pour un visuel professionnel
    sns.set(style="whitegrid")
    # Création du barplot pour les prix moyens mensuels
    plt.figure(figsize=(14, 8))
    sns.barplot(x='Month-Year', y='Day-ahead Price [EUR/MWh]', data=monthly_avg, palette='viridis')
    # Rotation des étiquettes de l'axe X pour une meilleure lisibilité
    plt.xticks(rotation=90, fontsize=10)
    # Ajout de titres et d'étiquettes
    plt.xlabel('Month-year', fontsize=14)
    plt.ylabel('Average price [EUR/MWh]', fontsize=14)
    # Ajustement automatique des espacements pour éviter la superposition
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Average_electricity_price.png"), dpi=400)
    
def heatmap_plot(price_df, output_dir_plot):
    df2 = price_df.copy()
    df2['Time'] = pd.to_datetime(df2['Time'], format='%d/%m/%Y %H:%M')
    df2['Hour'] = df2['Time'].dt.hour
    df2['Day_of_Year'] = df2['Time'].dt.dayofyear
    df2['Year'] = df2['Time'].dt.year
    # Calcul des prix moyens par heure et jour de l'année (agrégation par heure et jour)
    heatmap_data = df2.groupby(['Day_of_Year', 'Hour'])['Day-ahead Price [EUR/MWh]'].mean().unstack()
    # Configuration de style pour un visuel professionnel
    sns.set(style="whitegrid")
    # Création de la heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, cmap='coolwarm', cbar_kws={'label': 'Average price [EUR/MWh]'})
    # Ajout de titres et d'étiquettes
    plt.xlabel('Hour of day', fontsize=14)
    plt.ylabel('Day of year', fontsize=14)
    # Affichage de la figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Heatmap_electricity_price.png"), dpi=400)
    
    return None 

def heatmap_plot_2(price_df, output_dir_plot):
    df2 = price_df.copy()
    df2['Time'] = pd.to_datetime(df2['Time'], format='%d/%m/%Y %H:%M')
    df2['Hour'] = df2['Time'].dt.hour
    
    # Création d'une colonne Année-Mois pour l'axe Y
    df2['Year_Month'] = df2['Time'].dt.strftime('%Y-%m')
    
    # Calcul des prix moyens par heure et par Année-Mois (agrégation par heure et mois)
    heatmap_data = df2.groupby(['Year_Month', 'Hour'])['Day-ahead Price [EUR/MWh]'].mean().unstack()
    
    # Configuration de style pour un visuel professionnel
    sns.set(style="whitegrid")
    
    # Création de la heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, cmap='coolwarm', cbar_kws={'label': 'Average price [EUR/MWh]'})
    
    # Ajout de titres et d'étiquettes
    plt.xlabel('Hour of day', fontsize=14)
    plt.ylabel('Year-Month', fontsize=14)
    
    # Amélioration de la mise en page
    plt.tight_layout()
    
    # Sauvegarde du graphique dans un fichier PNG avec haute résolution
    plt.savefig(os.path.join(output_dir_plot, "Heatmap_electricity_price_2.png"), dpi=400)
    
    return None

def heatmap_month_plot(price_df, output_dir_plot):
    df3 = price_df.copy()
    df3['Time'] = pd.to_datetime(df3['Time'], format='%d/%m/%Y %H:%M')
    # Extraction des informations sur les heures, jours et mois
    df3['Hour'] = df3['Time'].dt.hour
    df3['Day'] = df3['Time'].dt.day
    df3['Month'] = df3['Time'].dt.month
    df3['Month_Name'] = df3['Time'].dt.strftime('%B')  # Nom du mois pour les labels
    # Initialisation de la figure 4x3 pour les sous-graphes (subplots)
    fig, axes = plt.subplots(4, 3, figsize=(16, 12))
    # Palette de couleurs pour la heatmap
    cmap = 'coolwarm'
    # Boucle sur chaque mois de l'année
    for i, month in enumerate(range(1, 13)):
        # Filtrage des données pour le mois courant
        monthly_data = df3[df3['Month'] == month]
        
        # Calcul des prix moyens par jour et par heure pour le mois courant
        heatmap_data = monthly_data.groupby(['Day', 'Hour'])['Day-ahead Price [EUR/MWh]'].mean().unstack()
        
        # Sélection de l'axe correct dans la grille 4x3
        ax = axes[i // 3, i % 3]
        
        # Tracé de la heatmap pour le mois courant
        sns.heatmap(heatmap_data, ax=ax, cmap=cmap, cbar_kws={'label': 'Price [EUR/MWh]'}, cbar=(i == 11))  # Cbar uniquement pour le dernier subplot
        
        # Ajout du titre pour chaque mois
        ax.set_title(df3['Month_Name'].unique()[i], fontsize=14)
        
        # Étiquettes des axes
        ax.set_xlabel('Hour', fontsize=10)
        ax.set_ylabel('Day', fontsize=10)
    # Ajustement des espaces entre les subplots
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(os.path.join(output_dir_plot, "Heatmap_electricity_price_monthly.png"), dpi=400)
    
def heatmap_month_plot_2(price_df, output_dir_plot ):
    
    import matplotlib.gridspec as gridspec
    df4=price_df.copy()
    df4['Time'] = pd.to_datetime(df4['Time'], format='%d/%m/%Y %H:%M')

    # Extraction des informations sur les heures, jours et mois
    df4['Hour'] = df4['Time'].dt.hour
    df4['Day'] = df4['Time'].dt.day
    df4['Month'] = df4['Time'].dt.month
    df4['Month_Name'] = df4['Time'].dt.strftime('%B')  # Nom du mois pour les labels

    # Initialisation de la figure 4x3 avec un subplot supplémentaire pour le cbar
    fig = plt.figure(figsize=(16, 12))
    #fig.suptitle('Carte thermique des prix horaires par mois (Bidding Zone Allemagne)', fontsize=18)

    # Utilisation de Gridspec pour une gestion plus fine des sous-graphes
    gs = gridspec.GridSpec(4, 4, width_ratios=[1, 1, 1, 0.05], wspace=0.3, hspace=0.4)

    # Palette de couleurs pour la heatmap
    cmap = 'coolwarm'

    # Initialisation d'une variable pour stocker l'objet colormap (nécessaire pour le cbar global)
    vmin = df4['Day-ahead Price [EUR/MWh]'].min()
    vmax = df4['Day-ahead Price [EUR/MWh]'].max()

    # Boucle sur chaque mois de l'année
    for i, month in enumerate(range(1, 13)):
        # Filtrage des données pour le mois courant
        monthly_data = df4[df4['Month'] == month]
        
        # Calcul des prix moyens par jour et par heure pour le mois courant
        heatmap_data = monthly_data.groupby(['Day', 'Hour'])['Day-ahead Price [EUR/MWh]'].mean().unstack()
        
        # Sélection de l'axe correct dans la grille 4x3 (la 4ème colonne est réservée au cbar)
        ax = plt.subplot(gs[i // 3, i % 3])
        
        # Tracé de la heatmap pour le mois courant sans cbar
        sns.heatmap(heatmap_data, ax=ax, cmap=cmap, cbar=False, vmin=vmin, vmax=vmax)
        
        # Ajout du titre pour chaque mois
        ax.set_title(df4['Month_Name'].unique()[i], fontsize=14)
        
        # Étiquettes des axes
        ax.set_xlabel('Heure de la journée', fontsize=10)
        ax.set_ylabel('Jour du mois', fontsize=10)

    # Création d'un seul cbar à droite sans recréer une nouvelle heatmap
    cbar_ax = plt.subplot(gs[:, 3])  # Utilisation de toute la dernière colonne pour le cbar
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Array vide car la heatmap est déjà tracée
    cbar = plt.colorbar(sm, cax=cbar_ax)
    cbar.set_label('Prix [EUR/MWh]', fontsize=12)

    # Ajustement de l'espacement de la figure
    plt.tight_layout(rect=[0, 0, 0.95, 0.95])
    plt.savefig(os.path.join(output_dir_plot, "Heatmap_electricity_price_monthly_2.png"), dpi=400)
    
    
def heatmap_month_plot_3(price_df, output_dir_plot):
    import matplotlib.gridspec as gridspec
    df= price_df.copy()
    df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M')

    # Extraction des informations sur les heures, jours et mois
    df['Hour'] = df['Time'].dt.hour
    df['Day'] = df['Time'].dt.day
    df['Month'] = df['Time'].dt.month
    df['Month_Name'] = df['Time'].dt.strftime('%B')  # Nom du mois pour les labels

    # Initialisation de la figure 4x3 avec un subplot supplémentaire pour le cbar
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle('Carte thermique des prix horaires par mois (Bidding Zone Allemagne)', fontsize=18)

    # Utilisation de Gridspec pour une gestion plus fine des sous-graphes
    gs = gridspec.GridSpec(4, 4, width_ratios=[1, 1, 1, 0.05], wspace=0.3, hspace=0.4)

    # Palette de couleurs pour la heatmap
    cmap = 'coolwarm'

    # Variables pour les limites du colorbar
    vmin = df['Day-ahead Price [EUR/MWh]'].min()
    vmax = df['Day-ahead Price [EUR/MWh]'].max()

    # Boucle sur chaque mois de l'année
    for i, month in enumerate(range(1, 13)):
        # Filtrage des données pour le mois courant
        monthly_data = df[df['Month'] == month]
        
        # Calcul des prix moyens par jour et par heure pour le mois courant
        heatmap_data = monthly_data.groupby(['Day', 'Hour'])['Day-ahead Price [EUR/MWh]'].mean().unstack()
        
        # Sélection de l'axe correct dans la grille 4x3 (la 4ème colonne est réservée au cbar)
        ax = plt.subplot(gs[i // 3, i % 3])
        
        # Tracé de la heatmap pour le mois courant sans cbar
        sns.heatmap(heatmap_data, ax=ax, cmap=cmap, cbar=False, vmin=vmin, vmax=vmax)
        
        # Ajout du titre pour chaque mois
        ax.set_title(df['Month_Name'].unique()[i], fontsize=14)
        
        # Ajouter les étiquettes des axes uniquement pour les sous-graphes extrêmes
        if i % 3 == 0:  # Si on est dans la colonne de gauche (1ère colonne), afficher l'étiquette Y
            ax.set_ylabel('Jour du mois', fontsize=10)
        else:
            ax.set_ylabel('')  # Supprimer l'étiquette Y
        
        if i // 3 == 3:  # Si on est dans la dernière ligne (4ème ligne), afficher l'étiquette X
            ax.set_xlabel('Heure de la journée', fontsize=10)
        else:
            ax.set_xlabel('')  # Supprimer l'étiquette X

    # Création d'un seul cbar à droite pour toute la figure
    cbar_ax = plt.subplot(gs[:, 3])  # Utilisation de toute la dernière colonne pour le cbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    cbar = plt.colorbar(sm, cax=cbar_ax)
    cbar.set_label('Prix [EUR/MWh]', fontsize=12)

    # Ajustement de l'espacement de la figure
    plt.tight_layout(rect=[0, 0, 0.95, 0.95])
    plt.savefig(os.path.join(output_dir_plot, "Heatmap_electricity_price_monthly_3.png"), dpi=400)
    return None 


def volatility_heatmap(price_df, output_dir_plot):
    
    df = price_df.copy()
    
    # Conversion de la colonne 'Time' en format datetime
    df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M')
    
    # Extraction des heures, semaines et mois
    df['Hour'] = df['Time'].dt.hour
    df['Week'] = df['Time'].dt.strftime('%Y-%U')  # Année et numéro de semaine
    
    # Calcul de l'écart-type (volatilité) des prix par semaine et par heure
    volatility_data = df.groupby(['Week', 'Hour'])['Day-ahead Price [EUR/MWh]'].std().unstack()
    
    # Configuration de style pour un visuel professionnel
    sns.set(style="whitegrid")
    
    # Création de la heatmap avec normalisation de l'échelle de couleur
    plt.figure(figsize=(10, 8))
    sns.heatmap(volatility_data, cmap='coolwarm', 
                cbar_kws={'label': 'Volatility (Price Std. Dev.) [EUR/MWh]'}, 
                vmin=0, vmax=volatility_data.max().max())  # Limites de couleur ajustées
    
    # Ajout de titres et d'étiquettes
    #plt.title('Heatmap de la volatilité des prix par semaine et heure', fontsize=16)
    plt.xlabel('Hour', fontsize=14)
    plt.ylabel('Week', fontsize=14)
    
    # Amélioration de la mise en page
    plt.tight_layout()
    
    # Sauvegarde de la figure
    plt.savefig(os.path.join(output_dir_plot, "Heatmap_price_volatility_weekly.png"), dpi=400)

    return None    


def rolling_volatility_plot(price_df, output_dir_plot):
    df = price_df.copy()
    
    # Conversion de la colonne 'Time' en format datetime
    df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M')
    
    # Calcul de la volatilité glissante (écart-type sur une fenêtre de 24 heures)
    df.set_index('Time', inplace=True)
    df['Rolling Volatility (24H)'] = df['Day-ahead Price [EUR/MWh]'].rolling(window=24).std()
    
    # Création du graphique en ligne
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['Rolling Volatility (24H)'], color='blue', linewidth=1.5)
    
    # Ajout de titres et d'étiquettes
    #plt.title('Volatilité glissante des prix horaires (24 heures)', fontsize=16)
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Volatility (Std) [EUR/MWh]', fontsize=14)
    
    # Amélioration de la mise en page
    plt.tight_layout()
    
    # Sauvegarde du graphique
    plt.savefig(os.path.join(output_dir_plot, "Rolling_Volatility_24H.png"), dpi=400)
    return None


def boxplot_prices(price_df, output_dir_plot):
    df = price_df.copy()
    
    # Conversion de la colonne 'Time' en format datetime
    df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M')
    
    # Extraction des périodes pertinentes
    df['Day'] = df['Time'].dt.date  # Extraction du jour complet
    df['Week'] = df['Time'].dt.strftime('%Y-%U')  # Année et numéro de semaine
    df['Month'] = df['Time'].dt.strftime('%Y-%m')  # Année et mois

    # Configuration de style pour un visuel professionnel
    sns.set(style="whitegrid")

    # 1. Boxplot par jour
    plt.figure(figsize=(15, 6))
    sns.boxplot(x='Day', y='Day-ahead Price [EUR/MWh]', data=df)
    plt.xticks(rotation=90)  # Rotation des étiquettes pour une meilleure lisibilité
    #plt.title('Boxplot des prix par jour', fontsize=16)
    plt.xlabel('Day', fontsize=14)
    plt.ylabel('Price [EUR/MWh]', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Boxplot_Price_Per_Day.png"), dpi=400)


    # 2. Boxplot par semaine
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='Week', y='Day-ahead Price [EUR/MWh]', data=df)
    plt.xticks(rotation=90)  # Rotation des étiquettes pour une meilleure lisibilité
    #plt.title('Boxplot des prix par semaine', fontsize=16)
    plt.xlabel('Week', fontsize=14)
    plt.ylabel('Price [EUR/MWh]', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Boxplot_Price_Par_Week.png"), dpi=400)
    

    # 3. Boxplot par mois
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='Month', y='Day-ahead Price [EUR/MWh]', data=df)
    plt.xticks(rotation=90)  # Rotation des étiquettes pour une meilleure lisibilité
    #plt.title('Boxplot des prix par mois', fontsize=16)
    plt.xlabel('Month', fontsize=14)
    plt.ylabel('Price [EUR/MWh]', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Boxplot_Price_Per_Mont.png"), dpi=400)
    

    return None



def plotStorageDispatchCases(scenario_cases, STORAGE_RESULT, selected_years, params):
    
    year_plot= int(params[scenario_cases[0]]['global']['plot']['year_plot'])
    start_hour=int(params[scenario_cases[0]]['global']['plot']['start_hour'])
    end_hour= int(params[scenario_cases[0]]['global']['plot']['end_hour'])
    
    #Plot hourly storage dipatch for each scenario 
    
    #for each scenario
    TEMP2= STORAGE_RESULT.copy()
    
    output_dir_plot = 'results/plots/storage_dispatch'
    os.makedirs(output_dir_plot, exist_ok=True)
    
    TEMP1= STORAGE_RESULT.copy()
    for scenario in scenario_cases:
        df = TEMP1[scenario].loc[(TEMP1[scenario]['year'] == year_plot) & (TEMP1[scenario]['hour'].between(start_hour, end_hour))]; df = df.set_index('hour')
        # Plot Storage dispatch
        labels_storage = ['charge', 'discharge', 'tariff_level']
        colors_storage= ['hotpink', 'darkcyan', 'black']
        fig_storagedispatch, ax1= hourlyStorageDispatch(labels_storage, colors_storage, df_area=df[['Pc', 'Pd']], df_line=df[['tariff']], sto_level=True, legend=True)
        fig_storagedispatch.savefig(os.path.join(output_dir_plot, f'storage_dispatch_{scenario}.png'), dpi=350)
    
    
    #for all scenarios 
    num_scenarios = len(scenario_cases)
    labels_storage = ['charge', 'discharge', 'tariff_level']
    colors_storage = ['hotpink', 'darkcyan', 'black']

    fig, axes = plt.subplots(num_scenarios, 1, figsize=(15, 4 * num_scenarios), sharex=True, sharey=True)
    scenarios_labels = {scenario_cases[0]: params[scenario_cases[0]]['global']['tariff']['shape'],
                        scenario_cases[1]: params[scenario_cases[1]]['global']['tariff']['shape'],
                        scenario_cases[2]: params[scenario_cases[2]]['global']['tariff']['shape'],
                        scenario_cases[3]: params[scenario_cases[3]]['global']['tariff']['shape'],
                        }
     
    for i, scenario in enumerate(scenario_cases):
        df = STORAGE_RESULT[scenario].loc[(STORAGE_RESULT[scenario]['year'] == year_plot) & (STORAGE_RESULT[scenario]['hour'].between(start_hour, end_hour))]
        df = df.set_index('hour')

        ax = axes[i] if num_scenarios > 1 else axes  
        if scenarios_labels[scenario]== params[scenario_cases[0]]['global']['tariff']['shape']:
            hourlyStorageDispatch_2(labels_storage, colors_storage, df_area=df[['Pc', 'Pd']], sto_level=False, legend=False, ax1=ax)
        else:
            hourlyStorageDispatch_2(labels_storage, colors_storage, df_area=df[['Pc', 'Pd']], df_line=df[['tariff']], sto_level=True, legend=False, ax1=ax)
        ax.set_title(f'{scenarios_labels[scenario]}')
    

    axes[-1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=num_scenarios*2, fontsize=12, frameon=False)

    plt.savefig(os.path.join(output_dir_plot, f'HourlystorageDispatchCombined.png'), dpi=350)    

    #Plot comparison storage dispatch vs price
    
    dispatch_price ={}
    
    
    for scenario in scenario_cases:
        #df1 = STORAGE_RESULT[scenario].loc[(STORAGE_RESULT[scenario]['year'] == year_plot)] 
        df1 = STORAGE_RESULT[scenario]
        dispatch = df1[['Pc', 'Pd', 'price']] 
        dispatch_price[scenario] = dispatch
    # First option: Charging and discgarging are separated
    fig_dispatchprice_1= plotStorageDispatchPrice(dispatch_price)
    fig_dispatchprice_1.savefig(os.path.join(output_dir_plot, f'storage_dispatch_price_comparison_{year_plot}.png'), dpi=350) 
    # second option: Charging and discgarging are combined
    fig_dispatchprice_2= plotStorageDispatchPrice_2(dispatch_price)
    fig_dispatchprice_2.savefig(os.path.join(output_dir_plot, f'storage_dispatch_price_comparison_2_{year_plot}.png'), dpi=400)

        
    #Tariff signal comparison
    tariff_signals = {}
    
    for scenario in scenario_cases[-3:]:
        df2 = STORAGE_RESULT[scenario].loc[(STORAGE_RESULT[scenario]['year'] == year_plot) & (STORAGE_RESULT[scenario]['hour'].between(start_hour, end_hour))]
        load_tariff = df2[['hour','tariff', 'net_load']] 
        tariff_signals[scenario] = load_tariff
    
    fig_tariffsignal= plotTariffSignals(tariff_signals)


    fig_tariffsignal.savefig(os.path.join(output_dir_plot, f'tariff_signals_comparison_{year_plot}.jpg'), dpi=600)
    
    netloadTariff={}
    
    for scenario in scenario_cases[-3:]:
        df3 = STORAGE_RESULT[scenario].loc[(STORAGE_RESULT[scenario]['year'] == year_plot)]
        netloadTariff[scenario]= df3
    fig_tariff_netload = plotNetloadtariff(netloadTariff)
    fig_tariff_netload.savefig(os.path.join(output_dir_plot, f'netload_tariff.jpg'), dpi=600)
    
    #Plot netload vs revenue
    combined_df1={}
    combined_df2={}
    combined_df ={}
    selected_df={}
    #for scenario, df in STORAGE_RESULT.items():
    # Concatenate DataFrames for each scenario
    combined_df1= pd.concat([df.assign(scenario=scenario) for scenario, df in STORAGE_RESULT.items()], ignore_index=True)
    # Convert 'year' column to string
    combined_df1['year'] = combined_df1['year'].astype(str)
    # Calculate profit
    combined_df1['profit'] = combined_df1['dispatch'] * combined_df1['price'] # without annual cap_cost and annual OM 
    # Map scenario names to selected tariffs
    #selected_tariff = ["flat", "proportional", "piecewise"]
    selected_tariff = [params[scenario_cases[1]]['global']['tariff']['shape'], 
                        params[scenario_cases[2]]['global']['tariff']['shape'], 
                        params[scenario_cases[3]]['global']['tariff']['shape']]
    scenario_tariff_mapping = {}
    for i, scenario in enumerate(scenario_cases[1:]):
        scenario_tariff_mapping[scenario] = selected_tariff[i]
    combined_df1['scenario'] = combined_df1['scenario'].replace(scenario_tariff_mapping)
    # Plot netload revenue line
    fig_profit_netload = plotNetloadRevenue_line(pd.DataFrame(combined_df1))
    # Write HTML file
    fig_profit_netload.write_html(os.path.join(output_dir_plot, f'netload_profit.html'))
    
    # Only revenue to avoid negetaive part
    
    combined_df2 = pd.concat([df.assign(scenario=scenario) for scenario, df in TEMP2.items()], ignore_index=True)
    combined_df2['year'] = combined_df2['year'].astype(str)
    combined_df2['revenue'] = combined_df2['Pd']*combined_df2['price']
    #selected_tariff = ["without tarif", "flat", "proportional", "piecewise"]
    selected_tariff = [ params[scenario_cases[0]]['global']['tariff']['shape'],
                        params[scenario_cases[1]]['global']['tariff']['shape'], 
                        params[scenario_cases[2]]['global']['tariff']['shape'], 
                        params[scenario_cases[3]]['global']['tariff']['shape']]
    scenario_tariff_mapping = {}
    for i, scenario in enumerate(scenario_cases):
        scenario_tariff_mapping[scenario] = selected_tariff[i]
    combined_df2['scenario'] = combined_df2['scenario'].replace(scenario_tariff_mapping)
    fig_revenue_netload = plotNetloadRevenue_line_2(pd.DataFrame(combined_df2))
    fig_revenue_netload.write_html(os.path.join(output_dir_plot, f'netload_revenue.html'))
    
    #Revenue vs tariff 
    fig_revenue_tariff= plotTariffRevenue_line(pd.DataFrame(combined_df2))
    fig_revenue_tariff.write_html(os.path.join(output_dir_plot, f'Tariff_revenue.html'))

    # Plot Storage dispatch vs price over years 
    selected_scenarios = scenario_cases[-3:]
    combined_df = pd.concat([df.assign(scenario=scenario) for scenario, df in STORAGE_RESULT.items()], ignore_index=True)
    combined_df['year'] = combined_df['year'].astype(str)
    selected_df = combined_df[(combined_df['scenario'].isin(selected_scenarios)) & (combined_df['year'].isin(selected_years[-2:]))]
    #scenario_mapping = {scenario_cases[0]: 'without tariff', scenario_cases[1]: 'flat ', scenario_cases[2]: 'proportional', scenario_cases[3]: 'piecewise'}
    scenario_mapping = {scenario_cases[0]: params[scenario_cases[0]]['global']['tariff']['shape'], 
                        scenario_cases[1]: params[scenario_cases[1]]['global']['tariff']['shape'], 
                        scenario_cases[2]: params[scenario_cases[2]]['global']['tariff']['shape'], 
                        scenario_cases[3]: params[scenario_cases[3]]['global']['tariff']['shape']}
    selected_df['scenario'] = selected_df['scenario'].replace(scenario_mapping)
    fig_dispatch_year = plotStorageDispatchYears(selected_years[-2:], selected_scenarios, pd.DataFrame(selected_df))
    fig_dispatch_year.write_html(os.path.join(output_dir_plot, f'storage_dispatch_tariff_comparison.html'))
    
    #Plot storage dispatch volume
    selected_scenarios = scenario_cases[-3:]
    combined_df = pd.concat([df.assign(scenario=scenario) for scenario, df in STORAGE_RESULT.items()], ignore_index=True)
    combined_df['year'] = combined_df['year'].astype(str)
    selected_df = combined_df[(combined_df['scenario'].isin(selected_scenarios)) & (combined_df['year'].isin(selected_years[-3:]))]
    #scenario_mapping = {scenario_cases[0]: 'without tariff', scenario_cases[1]: 'flat ', scenario_cases[2]: 'proportional', scenario_cases[3]: 'piecewise'}
    scenario_mapping = {scenario_cases[0]: params[scenario_cases[0]]['global']['tariff']['shape'], 
                        scenario_cases[1]: params[scenario_cases[1]]['global']['tariff']['shape'], 
                        scenario_cases[2]: params[scenario_cases[2]]['global']['tariff']['shape'], 
                        scenario_cases[3]: params[scenario_cases[3]]['global']['tariff']['shape']}
    selected_df['scenario'] = selected_df['scenario'].replace(scenario_mapping)
    fig_dispatch_year_2 = plotStorageDispatchYears_2(pd.DataFrame(selected_df))
    fig_dispatch_year_2.write_html(os.path.join(output_dir_plot, f'storage_dispatch_tariff_comparison_volume.html'))
    
    # Plot volume amount for all years
    selected_scenarios = scenario_cases[-4:]
    combined_df = pd.concat([df.assign(scenario=scenario) for scenario, df in STORAGE_RESULT.items()], ignore_index=True)
    combined_df['year'] = combined_df['year'].astype(str)
    selected_df = combined_df[(combined_df['scenario'].isin(selected_scenarios)) & (combined_df['year'].isin(selected_years[-3:]))]
    #scenario_mapping = {scenario_cases[0]: 'without tariff', scenario_cases[1]: 'flat ', scenario_cases[2]: 'proportional', scenario_cases[3]: 'piecewise'}
    scenario_mapping = {scenario_cases[0]: params[scenario_cases[0]]['global']['tariff']['shape'], 
                        scenario_cases[1]: params[scenario_cases[1]]['global']['tariff']['shape'], 
                        scenario_cases[2]: params[scenario_cases[2]]['global']['tariff']['shape'], 
                        scenario_cases[3]: params[scenario_cases[3]]['global']['tariff']['shape']}
    selected_df['scenario'] = selected_df['scenario'].replace(scenario_mapping)
    fig_dispatch_vol=plotDispatchVolume(pd.DataFrame(selected_df))
    fig_dispatch_vol.write_html(os.path.join(output_dir_plot, f'storage_dispatch_volume.html'))
        
    # compare revenue for all scenarios:    
    plot_revenue_comparison(STORAGE_RESULT, params, output_dir_plot)
    plot_tariff_revenue_comparison(STORAGE_RESULT, params, output_dir_plot) 
    plot_energy_comparison(STORAGE_RESULT, params, output_dir_plot)   
    plot_dispatch_heatmaps(STORAGE_RESULT,output_dir_plot, params, scenario_cases, year=year_plot)
    
    plot_dispatch_distribution(STORAGE_RESULT,output_dir_plot, params, scenario_cases, plot_type='violin')
    plot_dispatch_distribution(STORAGE_RESULT,output_dir_plot, params, scenario_cases, year=year_plot, plot_type='box')
   
    plot_dispatch_distribution_grid(STORAGE_RESULT, output_dir_plot, params, scenario_cases, plot_type='box')
    plot_dispatch_distribution_grid(STORAGE_RESULT, output_dir_plot, params, scenario_cases, plot_type='violin')
    plot_monthly_average_dispatch(STORAGE_RESULT, output_dir_plot, scenario_cases, params)
    plot_monthly_average_dispatch(STORAGE_RESULT, output_dir_plot, scenario_cases, params)
    return None 


def plot_dispatch_heatmaps(storage_results,output_dir_plot,params,scenario_cases, year=2015, figsize=(16, 16)):
    """
    Plots a 2x2 grid of heatmaps showing the dispatch patterns for each scenario in the given dictionary.
    
    Parameters:
    - storage_results (dict): Dictionary where keys are scenario names and values are DataFrames with dispatch data.
    - year (int): Year to filter the data for (default is 2023).
    - figsize (tuple): Size of the figure (default is (20, 12)).
    
    Each DataFrame in storage_results should have:
    - 'hour': Hour column (0-23, repeating daily)
    - 'dispatch': Dispatch power for the hour
    - 'year': Year column to filter the data
    
    Returns:
    - None. Displays the heatmap.
    """
    # Define a 2x2 plot grid
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = axes.flatten()  # Flatten to iterate over the 4 subplots easily
    
    # Calculate the number of days in the specified year
    num_days_in_year = 366 if pd.Timestamp(year=year, month=12, day=31).is_leap_year else 365

    scenarios_labels = {scenario_cases[0]: params[scenario_cases[0]]['global']['tariff']['shape'],
                        scenario_cases[1]: params[scenario_cases[1]]['global']['tariff']['shape'],
                        scenario_cases[2]: params[scenario_cases[2]]['global']['tariff']['shape'],
                        scenario_cases[3]: params[scenario_cases[3]]['global']['tariff']['shape'],
                        }

    # Loop over each scenario and plot in the corresponding subplot
    for i, (scenario_name, data) in enumerate(storage_results.items()):
        # Filter the data for the specified year
        data_year = data[data['year'] == year].copy()
        
        # Add 'day' column to group data into daily blocks
        data_year['day'] = (data_year['hour'] // 24) + 1  # Integer division to get day indices
        data_year['hour_of_day'] = data_year['hour'] % 24  # Modulus to get hour of each day (0-23)
        
        # Create an empty matrix with NaNs for missing values
        heatmap_data = np.full((num_days_in_year, 24), np.nan)  # Adjusted for leap/non-leap year
        
        # Populate the matrix with dispatch values
        for _, row in data_year.iterrows():
            day_idx = int(row['day']) - 1  # Convert to zero-indexed
            hour_idx = int(row['hour_of_day'])
            # Ensure the index does not exceed the matrix bounds
            if day_idx < num_days_in_year:
                heatmap_data[day_idx, hour_idx] = row['dispatch']
        
        # Plot heatmap for the current scenario
        sns.heatmap(heatmap_data, cmap="coolwarm", center=0, ax=axes[i], 
                    cbar_kws={'label': 'Dispatch Power (MW)'})
        axes[i].set_title(f"{scenarios_labels[scenario_name]}", fontsize=12)
        axes[i].set_xlabel("Hour of Day")
        axes[i].set_ylabel("Day of Year")
    
    # Adjust layout and add an overarching title
    plt.tight_layout()
    #plt.suptitle(f"Hourly Dispatch Heatmap for Different Tariff Scenarios in {year}", fontsize=16, y=1.02)
    plt.savefig(os.path.join(output_dir_plot, f'HEATMAP_STORAGE_DISPATCH_{year}.jpg'), dpi=400)
    return None

def plot_dispatch_distribution(storage_results,output_dir_plot, params, scenario_cases, year=2023, plot_type='box', figsize=(12, 8)):
    """
    Plots a box or violin plot for the dispatch distribution across different tariff scenarios.
    
    Parameters:
    - storage_results (dict): Dictionary where keys are scenario names and values are DataFrames with dispatch data.
    - year (int): Year to filter the data for (default is 2023).
    - plot_type (str): Type of plot - 'box' for box plot, 'violin' for violin plot (default is 'box').
    - figsize (tuple): Size of the figure (default is (12, 8)).
    
    Each DataFrame in storage_results should have:
    - 'dispatch': Dispatch power for the hour
    - 'year': Year column to filter the data
    
    Returns:
    - None. Displays the box or violin plot.
    """
    scenarios_labels = {scenario_cases[0]: params[scenario_cases[0]]['global']['tariff']['shape'],
                        scenario_cases[1]: params[scenario_cases[1]]['global']['tariff']['shape'],
                        scenario_cases[2]: params[scenario_cases[2]]['global']['tariff']['shape'],
                        scenario_cases[3]: params[scenario_cases[3]]['global']['tariff']['shape'],
                        }
    # Prepare the combined DataFrame for all scenarios for the specified year
    combined_data = []
    for scenario_name, data in storage_results.items():
        # Filter data by year and add a column for the scenario name
        scenario_data = data[data['year'] == year][['dispatch']].copy()
        scenario_data['Scenario'] = scenarios_labels[scenario_name]
        combined_data.append(scenario_data)
    
    # Concatenate all scenario data
    combined_df = pd.concat(combined_data)
    
    # Plot using seaborn based on specified plot type
    plt.figure(figsize=figsize)
    if plot_type == 'box':
        sns.boxplot(data=combined_df, x='Scenario', y='dispatch', palette="coolwarm")
        #plt.title(f"Box Plot of Storage Dispatch Across Scenarios for {year}")
    elif plot_type == 'violin':
        sns.violinplot(data=combined_df, x='Scenario', y='dispatch', palette="coolwarm", bw=0.2)
        #plt.title(f"Violin Plot of Storage Dispatch Across Scenarios for {year}")
    
    # Set labels
    plt.xlabel("Tariff Scenarios")
    plt.ylabel("Dispatch Power (MW)")
    plt.savefig(os.path.join(output_dir_plot, f'DISPATCH_DISTRIBUTION_{plot_type}.jpg'), dpi=400)
    return None



    
    
def plot_dispatch_distribution_grid_1(storage_results, output_dir_plot, params, scenario_cases, plot_type='box', figsize=(15, 15)):
    """
    Plots a 3x3 grid of box or violin plots for the dispatch distribution across different tariff scenarios for each unique year in the data.
    
    Parameters:
    - storage_results (dict): Dictionary where keys are scenario names and values are DataFrames with dispatch data.
    - output_dir_plot (str): Directory to save the output plot.
    - params (dict): Dictionary containing scenario parameters.
    - scenario_cases (list): List of scenario keys to use in the plot.
    - plot_type (str): Type of plot - 'box' for box plot, 'violin' for violin plot (default is 'box').
    - figsize (tuple): Size of the entire figure (default is (15, 15) for a 3x3 grid).
    
    Each DataFrame in storage_results should have:
    - 'dispatch': Dispatch power for the hour
    - 'year': Year column to filter the data.
    
    Returns:
    - None. Displays the 3x3 grid of box or violin plots.
    """
    # Define scenario labels
    scenarios_labels = {scenario_cases[0]: params[scenario_cases[0]]['global']['tariff']['shape'],
                        scenario_cases[1]: params[scenario_cases[1]]['global']['tariff']['shape'],
                        scenario_cases[2]: params[scenario_cases[2]]['global']['tariff']['shape'],
                        scenario_cases[3]: params[scenario_cases[3]]['global']['tariff']['shape'],
                        }
    
    # Retrieve all unique years in the dataset
    all_years = set()
    for data in storage_results.values():
        all_years.update(data['year'].unique())
    all_years = sorted(all_years)  # Sort years for consistent plotting order
    
    # Create subplots in a 3x3 grid
    num_years = len(all_years)
    fig, axes = plt.subplots(3, 3, figsize=figsize)
    axes = axes.flatten()  # Flatten for easy iteration over axes

    for idx, year in enumerate(all_years):
        if idx >= len(axes):
            break  # Stop if we have more years than subplots

        # Prepare the combined DataFrame for all scenarios for the current year
        combined_data = []
        for scenario_name, data in storage_results.items():
            # Filter data by the current year and add a column for the scenario name
            scenario_data = data[data['year'] == year][['dispatch']].copy()
            scenario_data['Scenario'] = scenarios_labels[scenario_name]
            combined_data.append(scenario_data)
        
        # Concatenate all scenario data for the current year
        combined_df = pd.concat(combined_data)
        
        # Select the current axis for plotting
        ax = axes[idx]
        if plot_type == 'box':
            sns.boxplot(data=combined_df, x='Scenario', y='dispatch', palette="coolwarm", medianprops={'color': 'red', 'linewidth': 2}, ax=ax)
        elif plot_type == 'violin':
            sns.violinplot(data=combined_df, x='Scenario', y='dispatch', palette="coolwarm", bw=0.2, ax=ax)
        
        # Set labels and title for the subplot
        ax.set_xlabel("Tariff Scenarios")
        ax.set_ylabel("Dispatch Power (MW)")
        ax.set_title(f"Year: {year}")
    
    # Hide any extra subplots if there are less than 9 years
    for j in range(num_years, len(axes)):
        axes[j].axis('off')

    # Adjust layout and save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, f'DISPATCH_DISTRIBUTION_grid_{plot_type}.jpg'), dpi=450)

    return None 

def plot_dispatch_distribution_grid(storage_results, output_dir_plot, params, scenario_cases, plot_type='box', figsize=(15, 15)):
    """
    Plots a 3x3 grid of box or violin plots for the dispatch distribution across different tariff scenarios for each unique year in the data.
    
    Parameters:
    - storage_results (dict): Dictionary where keys are scenario names and values are DataFrames with dispatch data.
    - output_dir_plot (str): Directory to save the output plot.
    - params (dict): Dictionary containing scenario parameters.
    - scenario_cases (list): List of scenario keys to use in the plot.
    - plot_type (str): Type of plot - 'box' for box plot, 'violin' for violin plot (default is 'box').
    - figsize (tuple): Size of the entire figure (default is (15, 15) for a 3x3 grid).
    
    Each DataFrame in storage_results should have:
    - 'dispatch': Dispatch power for the hour
    - 'year': Year column to filter the data.
    
    Returns:
    - None. Displays the 3x3 grid of box or violin plots.
    """
    # Define scenario labels
    scenarios_labels = {scenario_cases[0]: params[scenario_cases[0]]['global']['tariff']['shape'],
                        scenario_cases[1]: params[scenario_cases[1]]['global']['tariff']['shape'],
                        scenario_cases[2]: params[scenario_cases[2]]['global']['tariff']['shape'],
                        scenario_cases[3]: params[scenario_cases[3]]['global']['tariff']['shape'],
                        }
    
    # Retrieve all unique years in the dataset
    all_years = set()
    for data in storage_results.values():
        all_years.update(data['year'].unique())
    all_years = sorted(all_years)  # Sort years for consistent plotting order
    
    # Create subplots in a 3x3 grid
    num_years = len(all_years)
    fig, axes = plt.subplots(3, 3, figsize=figsize)
    axes = axes.flatten()  # Flatten for easy iteration over axes

    for idx, year in enumerate(all_years):
        if idx >= len(axes):
            break  # Stop if we have more years than subplots

        # Prepare the combined DataFrame for all scenarios for the current year
        combined_data = []
        for scenario_name, data in storage_results.items():
            # Filter data by the current year and add a column for the scenario name
            scenario_data = data[data['year'] == year][['dispatch']].copy()
            scenario_data['Scenario'] = scenarios_labels[scenario_name]
            combined_data.append(scenario_data)
        
        # Concatenate all scenario data for the current year
        combined_df = pd.concat(combined_data)
        
        # Select the current axis for plotting
        ax = axes[idx]
        if plot_type == 'box':
            sns.boxplot(data=combined_df, x='Scenario', y='dispatch', palette="coolwarm", medianprops={'color': 'red', 'linewidth': 2}, ax=ax)
        elif plot_type == 'violin':
            sns.violinplot(data=combined_df, x='Scenario', y='dispatch', palette="coolwarm", bw=0.2, ax=ax)
        
        # Set title for the subplot
        ax.set_title(f"Year: {year}")

        # Set the y-axis label only for the leftmost plots
        if idx % 3 == 0:  # Leftmost column
            ax.set_ylabel("Dispatch Power (MW)")
        else:
            ax.set_ylabel("")  # Empty y-label for other plots

        # Set the x-axis label only for the bottom row
        if idx >= 6:  # Bottom row
            ax.set_xlabel("Tariff Scenarios")
        else:
            ax.set_xlabel("")  # Empty x-label for other plots
    
    # Hide any extra subplots if there are less than 9 years
    for j in range(num_years, len(axes)):
        axes[j].axis('off')

    # Adjust layout and save the figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, f'DISPATCH_DISTRIBUTION_grid_{plot_type}.jpg'), dpi=450)

    return None


def plot_monthly_average_dispatch(storage_results, output_dir_plot, scenario_cases, params):
    """
    Plot monthly averages of dispatch (charging and discharging) for different scenarios based on hourly data.
    
    Parameters:
    - storage_results (dict): Dictionary where keys are scenario names and values are DataFrames with dispatch data.
    - output_dir_plot (str): Directory to save the plot.
    - scenario_cases (list): List of scenario names.
    - params (dict): Dictionary with scenario parameters for labels.
    
    Each DataFrame in storage_results should include:
    - 'dispatch': Dispatch power data.
    - 'hour': Hour of the year (0 to 8759).
    
    Returns:
    - None. Displays and saves the plot.
    """
    
    plt.figure(figsize=(14, 8))
    
    for scenario_name in scenario_cases:
        data = storage_results[scenario_name]
        data = data[data['year'] == 2021]
        
        
        # Calculate the month based on hour (approximate; assumes 30.4 days per month)
        data['month'] = (data['hour'] // (8760 // 12) + 1).astype(int)
        
        # Calculate monthly average dispatch
        monthly_avg_dispatch = data.groupby('month')['dispatch'].mean()
        
        # Retrieve the scenario label for the plot legend
        scenario_label = params[scenario_name]['global']['tariff']['shape']
        
        # Plot the monthly average for this scenario
        plt.plot(monthly_avg_dispatch.index, monthly_avg_dispatch.values, marker='o', label=scenario_label)
    
    # Set plot labels and title
    plt.xlabel("Month")
    plt.ylabel("Average Dispatch Power (MW)")
    plt.title("Monthly Average Dispatch Trends Across Scenarios")
    plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    plt.legend(title="Scenarios")
    plt.grid(True)

    # Save the plot
    plt.savefig(os.path.join(output_dir_plot, 'MONTLY_AVERAGE_DISPATCH.jpg'), dpi=400)
    return None


def plot_monthly_average_dispatch(storage_results, output_dir_plot, scenario_cases, params):
    """
    Plot monthly averages of dispatch (charging and discharging) for different scenarios based on hourly data.
    Displays each year in a 3x3 subplot grid.
    
    Parameters:
    - storage_results (dict): Dictionary where keys are scenario names and values are DataFrames with dispatch data.
    - output_dir_plot (str): Directory to save the plot.
    - scenario_cases (list): List of scenario names.
    - params (dict): Dictionary with scenario parameters for labels.
    
    Each DataFrame in storage_results should include:
    - 'dispatch': Dispatch power data.
    - 'hour': Hour of the year (0 to 8759).
    - 'year': The year of the data (e.g., 2015, 2016).
    
    Returns:
    - None. Displays and saves the plot.
    """
    
    years = sorted(storage_results[scenario_cases[0]]['year'].unique())  # Unique years in the data
    fig, axes = plt.subplots(3, 3, figsize=(18, 14), sharex=True, sharey=True)
    fig.suptitle("Monthly Average Dispatch Trends by Year Across Scenarios", fontsize=16)

    for i, year in enumerate(years):
        row, col = divmod(i, 3)  # Determine row and column for 3x3 subplot grid
        ax = axes[row, col]

        for scenario_name in scenario_cases:
            data = storage_results[scenario_name]
            data_year = data[data['year'] == year]

            # Calculate the month based on hour (approximate; assumes 30.4 days per month)
            data_year['month'] = (data_year['hour'] // (8760 // 12) + 1).astype(int)

            # Calculate monthly average dispatch
            monthly_avg_dispatch = data_year.groupby('month')['dispatch'].mean()

            # Retrieve the scenario label for the plot legend
            scenario_label = params[scenario_name]['global']['tariff']['shape']

            # Plot the monthly average for this scenario
            ax.plot(monthly_avg_dispatch.index, monthly_avg_dispatch.values, marker='o', label=scenario_label)

        # Set subplot title and labels
        ax.set_title(f"Year {year}")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        ax.grid(True)

    # Set common labels
    fig.text(0.5, 0.04, 'Month', ha='center', fontsize=12)
    fig.text(0.04, 0.5, 'Average Dispatch Power (MW)', va='center', rotation='vertical', fontsize=12)

    # Add a single legend for all subplots
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=len(scenario_cases), title="Scenarios")

    # Adjust layout and save the plot
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(os.path.join(output_dir_plot, 'MONTLY_AVERAGE_DISPATCH_3x3.jpg'), dpi=400)
    return None



def plotStorageDispatchSensitivitydelta(params, STORAGE_RESULT, categories):
    
    output_dir_plot = 'results/plots/storage_dispatch'
    os.makedirs(output_dir_plot, exist_ok=True)
    #average revenue for sensitivity on delta 
    plot_storage_revenues(STORAGE_RESULT, params, categories, output_dir_plot)
    #stacked revenues for snesitivity on delta 
    plot_stacked_revenues(STORAGE_RESULT, params, output_dir_plot)
    # Stacked market and Tariff revenue only
    plot_stacked_revenues_2(STORAGE_RESULT, params, output_dir_plot)
    # stacked bars with percentage
    plot_stacked_revenues_3(STORAGE_RESULT, params, output_dir_plot)

    return None


def plotStorageDispatchSensitivityShare(params, STORAGE_RESULT):
    
    output_dir_plot = 'results/plots/storage_dispatch'
    os.makedirs(output_dir_plot, exist_ok=True)
    plot_stacked_revenues_by_shape(STORAGE_RESULT, params, output_dir_plot)
    plot_stacked_revenues_by_shape_horizontal(STORAGE_RESULT, params, output_dir_plot)
    plot_stacked_revenues_by_shape_vertical(STORAGE_RESULT, params, output_dir_plot)

    return None 



def plotStorageConfiguration(scenario_cases, STORAGE_RESULT, params):
    
    output_dir_plot = 'results/plots/storage_dispatch'
    os.makedirs(output_dir_plot, exist_ok=True)
    # Compare Storage dispatch from ex-ante and ex-post tariff 
    plotStorageDispatchConfiguration(scenario_cases, STORAGE_RESULT, params, output_dir_plot)
    plotStorageDispatchConfiguration_2(scenario_cases, STORAGE_RESULT, params, output_dir_plot)
    
    
    # Create a dictionary to map shapes to subplot indices
    shape_to_idx = {}
    shape_counter = 0
    
    # Initialize the figure and axes
    fig, axs = plt.subplots(2, 1, figsize=(8, 7))
    
    colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']  # List of colors for different configurations
    config_color_map = {}  # Map to track the colors used for each config in each shape
    
    for scenario, df in STORAGE_RESULT.items():
        # Extracting the data
        df['revenue_net'] = df['dispatch'] * df['price']
        annual_revenue = df.groupby('year')['revenue_net'].sum().tolist()
        
        # Calculate mean revenue
        mean_revenue = np.mean(annual_revenue)
        
        config = params[scenario]['global']['tariff']['configuration']
        shape = params[scenario]['global']['tariff']['shape']
        
        # Map the shape to an index if it's not already mapped
        if shape not in shape_to_idx:
            shape_to_idx[shape] = shape_counter
            shape_counter += 1
        
        # Ensure unique colors for each configuration within the same shape
        if shape not in config_color_map:
            config_color_map[shape] = {}
        
        if config not in config_color_map[shape]:
            color_index = len(config_color_map[shape]) % len(colors)
            config_color_map[shape][config] = colors[color_index]
        
        # Select the correct axis for the current shape
        ax = axs[shape_to_idx[shape]]
        years = df['year'].unique()
        color = config_color_map[shape][config]  # Use the assigned color for this config
        
        ax.plot(years, annual_revenue, marker='o', color=color, label=f'Annual Revenues ({config})')
        ax.axhline(mean_revenue, color=color, linestyle='--', label=f'Mean Revenue ({config})')
        
        # Add titles and labels
        ax.set_title(f'{shape}')
        
        # Display x-axis label only on the bottom subplot
        if shape_to_idx[shape] == 1:
            ax.set_xlabel('Year')
        
        # Display y-axis label only on the left subplot
        if shape_to_idx[shape] == 0:
            ax.set_ylabel('Revenue (EUR)')
        
        ax.legend()
        ax.grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "ex-ante_ex-post_revenue_comparison.png"), dpi=400)
    
    return None




#.............................HELPER FUNCTIONS.............................................

def hourlyStorageDispatch(labels, colors, sto_level=False, df_area=None, df_line=None, legend=True, legend_position='upper center', legend_col_no=8, figsize=(15,6), bottom_fix=0.3, fontsize=12, ticksize=12, legfontsize=12 ):
    
    fig, ax1 = plt.subplots(figsize=figsize)
    ax2=ax1.twinx()
    # Stacked area plot
    x = range(int(df_area.index[0]), int(df_area.index[-1])+1)
    df_area_neg, df_area_pos = df_area.clip(upper=0), df_area.clip(lower=0)
    y_pos = [df_area_pos[c].tolist() for c in df_area_pos]
    y_neg = [df_area_neg[c].tolist() for c in df_area_neg]
    area1 = ax1.stackplot( x, y_pos, labels=labels, colors=colors, step='mid')
    area2 = ax1.stackplot( x, y_neg, colors=colors, step='mid')
    if sto_level:
        # line plot1
        line1 = ax2.plot(df_line, color='#434566', linestyle='-.', label='tariff level')
    
    if legend: 
        figs= area1+area2
        if sto_level:
            figs=area1 + area2 + line1 
        labels_all=[f.get_label() for f in figs]
        leg = ax1.legend(figs, labels_all, loc=legend_position, bbox_to_anchor=(0.5, -0.25), ncol=legend_col_no, fontsize=legfontsize, frameon=False)

    # properties
    ax1.set_xlabel('hour', fontsize=fontsize) 
    ax1.set_ylabel('MW', fontsize=fontsize)
    if sto_level:
        ax2.set_ylabel('EUR/MWh', fontsize=fontsize)
    ax1.tick_params(axis='both', which='major', labelsize=ticksize)
    ax2.tick_params(axis='y', which='major', labelsize=ticksize)
    
    plt.margins(x=0)
    plt.tight_layout()
    plt.subplots_adjust(bottom=bottom_fix, top=0.98, left=0.05, right=0.95)
    
    return fig, ax1


def hourlyStorageDispatch_2(labels, colors, sto_level=False, df_area=None, df_line=None, legend=True, legend_position='upper center', legend_col_no=8, figsize=(15.2,5.6), bottom_fix=0.1, fontsize=12, ticksize=12, legfontsize=12, ax1=None):
    if ax1 is None:
        fig, ax1 = plt.subplots(figsize=figsize)
        ax2 = ax1.twinx()
    else:
        ax2 = ax1.twinx()
    
    x = range(int(df_area.index[0]), int(df_area.index[-1]) + 1)
    df_area_neg, df_area_pos = df_area.clip(upper=0), df_area.clip(lower=0)
    y_pos = [df_area_pos[c].tolist() for c in df_area_pos]
    y_neg = [df_area_neg[c].tolist() for c in df_area_neg]
    area1 = ax1.stackplot(x, y_pos, labels=labels, colors=colors, step='mid')
    area2 = ax1.stackplot(x, y_neg, colors=colors, step='mid')
    if sto_level:
        line1 = ax2.plot(df_line, color='#434566', linestyle='-', label='tariff level')
    
    if legend:
        figs = area1 + area2
        if sto_level:
            figs = area1 + area2 + line1 
        labels_all = [f.get_label() for f in figs]
        leg = ax1.legend(figs, labels_all, loc=legend_position, bbox_to_anchor=(0.5, -0.25), ncol=legend_col_no, fontsize=legfontsize, frameon=False)

    ax1.set_xlabel('hours', fontsize=fontsize) 
    ax1.set_ylabel('Power [MW]', fontsize=fontsize)
    if sto_level:
        ax2.set_ylabel('Tariff [EUR/MWh]', fontsize=fontsize)
    ax1.tick_params(axis='both', which='major', labelsize=ticksize)
    ax2.tick_params(axis='y', which='major', labelsize=ticksize)
    
    plt.margins(x=0)
    plt.tight_layout()
    plt.subplots_adjust(bottom= bottom_fix, top=0.98, left=0.05, right=0.95)
    
    

    if ax1 is None:
        return fig, ax1
    else:
        return ax1



def plotStorageDispatchPrice(data): 
    
    fig, axs = plt.subplots(2, 2, figsize=(9, 9))
    fig.suptitle(' Storage dispatch vs prices')
    scenarios  = list(data.keys())
    
    tariff_types = ['without tariff', 'flat tariff', 'proportional tariff', 'piecewise tariff']

    for i, scenario in enumerate(scenarios):
        
        row = i // 2
        col = i % 2
        ax = axs[row, col]
        
        ax.scatter(data[scenario]['price'], data[scenario]['Pc'], label='Pc', color='blue', s=22)
        ax.scatter(data[scenario]['price'], data[scenario]['Pd'], label='Pd', color='red', s=22)
        
        ax.set_title(f'{tariff_types[i]}')
        ax.set_xlabel('Price')
        ax.set_ylabel('Pd/Pc')
        ax.legend()
        ax.tick_params(axis='both', labelsize=7)
        
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    return plt.gcf()



def plotStorageDispatchPrice_2(data): 
    
    fig, axs = plt.subplots(2, 2, figsize=(9, 9))
    fig.suptitle(' Storage dispatch vs prices')
    scenarios  = list(data.keys())
    
    tariff_types = ['without tariff', 'flat tariff', 'proportional tariff', 'piecewise tariff']

    for i, scenario in enumerate(scenarios):
        
        row = i // 2
        col = i % 2
        ax = axs[row, col]
        
        ax.scatter(data[scenario]['price'], data[scenario]['Pc'] + data[scenario]['Pd'] , label='Pd-Pc', color='blue')

        ax.set_title(f'{tariff_types[i]}')
        ax.set_xlabel('Price (EUR/MWh)')
        ax.set_ylabel('Pd-Pc (MW)')
        ax.legend()
        ax.tick_params(axis='both', labelsize=7)
        
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    return plt.gcf()



def plotTariffSignals(tariff_signals):
    num_scenarios = len(tariff_signals)
    scenario_labels = ["flat", "proportional", "piecewise"]

    # Plot setup
    fig, axes = plt.subplots(1, num_scenarios, figsize=(3.5* num_scenarios, 3.5))

    for i, (scenario_name, scenario_data) in enumerate(tariff_signals.items()):
        ax = axes[i] if num_scenarios > 1 else axes  # Handle single scenario case

        # Extract data
        tariff = scenario_data['tariff']
        net_load = scenario_data['net_load']
        hour = scenario_data['hour']
        ax.set_title(f'{scenario_labels[i]}')
        
        label = scenario_labels[i]

        # Plot tariff on the first y-axis
        ax.plot(hour, tariff, label=f'{label}', color='blue', linestyle='-', marker='o', markersize=2)
        ax.set_xlabel('Hours')
        ax.set_ylabel('Tariff (EUR/MWh)', color='blue')
        ax.tick_params('y', colors='blue')
        #ax.legend(loc='upper left')

        # Create a second y-axis that shares the same x-axis
        ax2 = ax.twinx()

        # Plot net_load on the second y-axis
        ax2.plot(hour, net_load, label='Net Load', color='brown')
        ax2.set_ylabel('Net Load (MW)', color='brown')
        ax2.tick_params('y', colors='brown')
        #ax2.legend(loc='upper right')
        
        # Set scalar formatter for y-axis
        #ax.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
        ax2.ticklabel_format(axis='y', style='sci', scilimits=(0,0))

        ax.tick_params(axis='both', labelsize=8)

    plt.tight_layout(rect=[0, 0, 1, 1])
    return plt.gcf()


def plotNetloadtariff(data):
    fig, axs = plt.subplots(1, 3, figsize=(11, 4))
    
    tariff_types = ['flat', 'proportional', 'piecewise']

    for i, (scenario, df_scenario) in enumerate(data.items()):
        ax = axs[i]

        ax.scatter(df_scenario['net_load'], df_scenario['tariff'], s=12, alpha=.9)
        ax.set_title(f'{tariff_types[i]}')
        ax.set_xlabel('Net Load (MW)')
        ax.set_ylabel('Tariff (EUR/MWh)')

        # Masquer les bords supérieur et droit du subplot
        ax.spines[['top', 'right']].set_visible(False)
        ax.ticklabel_format(axis='x', style='sci', scilimits=(0,0))

    # Ajuster la disposition pour éviter les chevauchements
    plt.tight_layout()

    return plt.gcf()



def plotNetloadRevenue_line(df):
    fig = px.line(df, x='net_load', y='profit', color='year', facet_col="scenario", labels={'net_load': 'Net load (MW)', 'profit': 'Profit (EUR/h)'})
    return fig


def plotNetloadRevenue_line_2(df):
    last_three_years = sorted(df['year'].unique())[-9:]
    filtered_df = df[df['year'].isin(last_three_years)]
    fig = px.line(filtered_df, x='net_load', y='revenue', color='year', facet_col="scenario", labels={'net_load': 'Net load (MW)', 'revenue': 'Revenue (EUR/h)'}, template="simple_white", width=960, height=600)
    return fig


def plotTariffRevenue_line(df):
    fig = px.line(df, x='tariff', y='revenue', color='year', facet_col="scenario", labels={'tariff': 'Tariff (EUR/MWh)', 'revenue': 'Revenue (EUR/h)'}, template="simple_white", width=960, height=600)
    return fig

def plotStorageDispatchYears(years, scenarios,df):
    fig = px.scatter(df, x='price', y='dispatch', facet_row="year", facet_col='scenario', facet_col_wrap=4, labels={'price': 'Price (EUR/MWh)', 'dispatch': 'Dispatch (MW)'})    
    return fig

def plotStorageDispatchYears_2(df):
    df['Pc'] = df['Pc'].abs()
    
    # Create scatter plot for Pd
    fig = px.scatter(df, x="price", y="dispatch", size="Pd", facet_row="year", facet_col="scenario", 
                     hover_name="year", log_x=False, size_max=60, width=900, height=800, labels={'price': 'Price (EUR/MWh)', 'dispatch': 'Energy (MWh)'}, template="simple_white")

    # Add trace for Pc with a different color
    num_traces = len(fig.data)
    for i in range(num_traces):
        fig.add_trace(px.scatter(df, x="price", y="dispatch", size="Pc", facet_row="year", facet_col="scenario", 
                             hover_name="year", log_x=False, size_max=60).update_traces(marker=dict(color='brown')).data[i])

    return fig


def plotDispatchVolume(df):
    df['Pc'] = df['Pc'].abs()
    
    grouped_df = df.groupby(["scenario", "year"]).agg({"Pd": "sum", "Pc": "sum"}).reset_index()
    grouped_df = grouped_df.rename(columns={"Pd": "discharged"})
    grouped_df = grouped_df.rename(columns={"Pc": "charged"})
    melted_df = pd.melt(grouped_df, id_vars=["scenario", "year"], value_vars=["discharged", "charged"], var_name="type", value_name="energy")
    
    fig = px.bar(melted_df, x="year", y="energy", color="year", facet_col="scenario", facet_row="type",
             labels={"energy": "Total Energy (MWh)", "year": "Year", "scenario": "Scenario", "type": "Type",},
             height=900, width=1080, template="simple_white")

    # Ajouter les valeurs sur les barres
    fig.update_traces(texttemplate='%{y:.2f}', textposition='outside')    
    return fig


def plot_revenue_comparison_ok(STORAGE_RESULT, params, output_dir_plot):
    alpha=0.85
    # Get all unique shapes
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4', 'grey']  # Colors for Tariff Revenue, Market Revenue, and Std Dev of Total Revenue
    bar_width = 0.3

    fig, ax = plt.subplots(figsize=(9, 7))

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    for shape in shapes:
        average_market_revenues = []
        average_tariff_revenues = []
        average_total_revenues = []
        std_total_revenues = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate revenues
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']

                # Calculate annual revenues
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum()
                total_revenue = annual_market_revenue + annual_tariff_revenue

                # Store values
                average_market_revenues.append(annual_market_revenue.mean())
                average_tariff_revenues.append(annual_tariff_revenue.mean())
                average_total_revenues.append(total_revenue.mean())
                std_total_revenues.append(total_revenue.std())

        # Convert lists to numpy arrays
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)
        average_total_revenues = np.array(average_total_revenues)
        std_total_revenues = np.array(std_total_revenues)

        # Indices for the bars
        index = np.arange(len(average_market_revenues))

        # Offset for the group of bars
        offset = shape_idx * bar_width * 2

        # Plot stacked bars for tariff and market revenues
        bars1 = ax.bar(index + offset, average_tariff_revenues, bar_width, color=colors[0], edgecolor='black', label='Tariff Revenue' if shape_idx == 0 else "", alpha=alpha)
        bars2 = ax.bar(index + offset, average_market_revenues, bar_width, bottom=average_tariff_revenues, color=colors[1], edgecolor='black', label='Market Revenue' if shape_idx == 0 else "", alpha=alpha)

        # Plot bars for standard deviation of total revenue
        bars3 = ax.bar(index + offset + bar_width, std_total_revenues, bar_width, color=colors[2], edgecolor='black', label='Std Dev of Total Revenue' if shape_idx == 0 else "", alpha=alpha)

        # Add annotations for tariff, market, and standard deviation revenues
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2
            ax.annotate(f'{height2:.2f}', xy=(bar2.get_x() + bar2.get_width() / 2, total_height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
        for bar in bars3:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

        # Add shape labels
        shapes_labels.extend([f'{shape}'])
        num_scenarios_per_shape.append(len(average_market_revenues))
        shape_idx += 1

    # Adjust tick positions and labels
    total_bars = sum(num_scenarios_per_shape)
    ticks_positions = np.arange(total_bars) * bar_width * 2 + bar_width / 2
    ax.set_xticks(ticks_positions)
    ax.set_xticklabels(shapes_labels, rotation=0, ha='right', fontsize=10)  # Increase tick label size

    ax.set_xlabel('Shapes', fontsize=10)  # Increase x-axis label size
    ax.set_ylabel('Revenue (EUR/y)', fontsize=10)  # Increase y-axis label size
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)  # Increase legend size

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "revenue_comparison.jpg"), dpi=600)





def plot_energy_comparison_1(STORAGE_RESULT, params, output_dir_plot):
    alpha = 0.85
    # Get all unique shapes (tariff designs)
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4']  # Color for energy stored and energy discharged
    hatches = ['///', '\\\\']  # Hatching patterns
    bar_width = 0.3  # Reduced bar width for less clutter

    fig, ax = plt.subplots(figsize=(9, 6))  # Adjusted figure size for readability
    
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(1.5)

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    # Variables to store the average energy stored and discharged for each tariff design
    avg_energy_stored_per_shape = []
    avg_energy_discharged_per_shape = []

    for shape in shapes:
        total_energy_stored = []
        total_energy_discharged = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate total energy stored (charging) and energy discharged (discharging)
                energy_stored = abs(df_delta[df_delta['dispatch']<0]['dispatch'].sum())  # Positive dispatch = charging
                energy_discharged = abs(df_delta[df_delta['dispatch']>0]['dispatch'].sum())  # Negative dispatch = discharging
                
                # Store the results
                total_energy_stored.append(energy_stored)
                total_energy_discharged.append(energy_discharged)

        # Convert lists to numpy arrays for easy bar plotting
        total_energy_stored = np.array(total_energy_stored)
        total_energy_discharged = np.array(total_energy_discharged)

        # Indices for the bars
        index = np.arange(len(total_energy_stored))

        # Offset for the group of bars, with spacing between scenarios
        offset = shape_idx * bar_width * 4  # Extra spacing between groups of scenarios

        # Plot bars for energy stored (charging)
        bars1_solid = ax.bar(index + offset, total_energy_stored, bar_width, color='none', edgecolor='black',
                       label='Energy Stored' if shape_idx == 0 else "", alpha=alpha)

        bars1_hatch = ax.bar(index + offset, total_energy_stored, bar_width, color='none', edgecolor=colors[0],
                             hatch=hatches[0], linewidth=0, alpha=1)

        # Plot bars for energy discharged (discharging)
        bars2_solid = ax.bar(index + offset + bar_width, total_energy_discharged, bar_width, color='none', edgecolor='black',
                       label='Energy Discharged' if shape_idx == 0 else "", alpha=alpha)

        bars2_hatch = ax.bar(index + offset + bar_width, total_energy_discharged, bar_width, color='none', edgecolor=colors[1],
                             hatch=hatches[1], linewidth=0, alpha=1)

        # Store average energy stored and discharged for the current tariff design
        avg_energy_stored_per_shape.append(np.mean(total_energy_stored))
        avg_energy_discharged_per_shape.append(np.mean(total_energy_discharged))

        # Add shape labels
        shapes_labels.extend([f'{shape}'])
        num_scenarios_per_shape.append(len(total_energy_stored))
        shape_idx += 1

    # Adjust tick positions and labels
    total_bars = sum(num_scenarios_per_shape)
    ticks_positions = np.arange(total_bars) * bar_width * 4 + bar_width / 2  # Add extra space between scenarios
    ax.set_xticks(ticks_positions)
    ax.set_xticklabels(shapes_labels, rotation=0, ha='right', fontsize=10)  # Increase tick label size

    ax.set_xlabel('Tariff Designs', fontsize=12)  # Increase x-axis label size
    ax.set_ylabel('Total Energy (MWh)', fontsize=12)  # Increase y-axis label size

    ax.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
    # Add trend lines
    # Convert shapes_labels to the corresponding x positions for the trend line (midpoints of the groups)
    trend_line_x_position_1 = np.arange(len(shapes)) * bar_width * 4 
    trend_line_x_position_2 = np.arange(len(shapes)) * bar_width * 4 + bar_width
    
    

    # Plot trend line for energy stored
    ax.plot(trend_line_x_position_1, avg_energy_stored_per_shape, marker='o', linestyle='-', color=colors[0], 
            label='Trend: Energy Stored')

    # Plot trend line for energy discharged
    ax.plot(trend_line_x_position_2, avg_energy_discharged_per_shape, marker='o', linestyle='-', color=colors[1], 
            label='Trend: Energy Discharged')

    # Move the legend to the bottom, outside the plot area
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=12)
    ax.grid(False)

    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to leave space for the legend
    plt.savefig(os.path.join(output_dir_plot, "energy_comparison_with_trend.png"), dpi=600)
    plt.close(fig)


def plot_energy_comparison(STORAGE_RESULT, params, output_dir_plot):
    alpha = 0.85
    # Get all unique shapes (tariff designs)
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4']  # Color for energy stored and energy discharged
    hatches = ['///', '\\\\']  # Hatching patterns
    bar_width = 0.3  # Reduced bar width for less clutter

    fig, ax = plt.subplots(figsize=(9, 6))  # Adjusted figure size for readability
    
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(1.5)

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    # Variables to store the average energy stored and discharged for each tariff design
    avg_energy_stored_per_shape = []
    avg_energy_discharged_per_shape = []

    for shape in shapes:
        total_energy_stored = []
        total_energy_discharged = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate total energy stored (charging) and energy discharged (discharging)
                energy_stored = abs(df_delta[df_delta['dispatch'] < 0]['dispatch'].sum())
                energy_discharged = abs(df_delta[df_delta['dispatch'] > 0]['dispatch'].sum())
                
                # Store the results
                total_energy_stored.append(energy_stored)
                total_energy_discharged.append(energy_discharged)

        # Convert lists to numpy arrays for easy bar plotting
        total_energy_stored = np.array(total_energy_stored)
        total_energy_discharged = np.array(total_energy_discharged)

        # Indices for the bars
        index = np.arange(len(total_energy_stored))

        # Offset for the group of bars, with spacing between scenarios
        offset = shape_idx * bar_width * 4  # Extra spacing between groups of scenarios

        # Plot bars for energy stored (charging)
        bars1_solid = ax.bar(index + offset, total_energy_stored, bar_width, color='none', edgecolor='black',
                       label='Energy Stored' if shape_idx == 0 else "", alpha=alpha)
        
        bars1_hatch = ax.bar(index + offset, total_energy_stored, bar_width, color='none', edgecolor=colors[0],
                             hatch=hatches[0], linewidth=0, alpha=1)

        # Plot bars for energy discharged (discharging)
        bars2_solid = ax.bar(index + offset + bar_width, total_energy_discharged, bar_width, color='none', edgecolor='black',
                       label='Energy Discharged' if shape_idx == 0 else "", alpha=alpha)
        
        bars2_hatch = ax.bar(index + offset + bar_width, total_energy_discharged, bar_width, color='none', edgecolor=colors[1],
                             hatch=hatches[1], linewidth=0, alpha=1)

        # Annotate each bar with its value above it, formatted in American style
        for bar in bars1_solid:
            ax.annotate(f'{bar.get_height():,.0f}',  # Add comma for thousands separator
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                        xytext=(0, 5),  # Adjust space above the bar
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, color=colors[0])
        
        for bar in bars2_solid:
            ax.annotate(f'{bar.get_height():,.0f}',  # Add comma for thousands separator
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                        xytext=(0, 5),  # Adjust space above the bar
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, color=colors[1])

        # Store average energy stored and discharged for the current tariff design
        avg_energy_stored_per_shape.append(np.mean(total_energy_stored))
        avg_energy_discharged_per_shape.append(np.mean(total_energy_discharged))

        # Add shape labels
        shapes_labels.extend([f'{shape}'])
        num_scenarios_per_shape.append(len(total_energy_stored))
        shape_idx += 1

    # Adjust y-axis to start at 4.10e5 for clearer comparison
    ax.set_ylim(4.10e5, None)
    
    # Adjust tick positions and labels
    total_bars = sum(num_scenarios_per_shape)
    ticks_positions = np.arange(total_bars) * bar_width * 4 + bar_width / 2
    ax.set_xticks(ticks_positions)
    ax.set_xticklabels(shapes_labels, rotation=0, ha='right', fontsize=10)

    ax.set_xlabel('Tariff Designs', fontsize=12)
    ax.set_ylabel('Total Energy (MWh)', fontsize=12)
    ax.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
    
    # Plot trend lines for average energy stored and discharged
    trend_line_x_position_1 = np.arange(len(shapes)) * bar_width * 4 
    trend_line_x_position_2 = np.arange(len(shapes)) * bar_width * 4 + bar_width
    
    ax.plot(trend_line_x_position_1, avg_energy_stored_per_shape, marker='o', linestyle='-', color=colors[0], 
            label='Trend: Energy Stored')
    
    ax.plot(trend_line_x_position_2, avg_energy_discharged_per_shape, marker='o', linestyle='-', color=colors[1], 
            label='Trend: Energy Discharged')

    # Move the legend to the bottom
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=12)
    ax.grid(False)

    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to leave space for the legend
    plt.savefig(os.path.join(output_dir_plot, "energy_comparison_with_trend.png"), dpi=600)
    plt.close(fig)
    
        
    
def plot_energy_comparison_OK(STORAGE_RESULT, params, output_dir_plot):
    alpha = 0.85
    # Get all unique shapes (tariff designs)
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4']  # Color for energy stored and energy discharged
    hatches = ['/', '\\']  # Hatching patterns
    bar_width = 0.15  # Reduced bar width for less clutter

    fig, ax = plt.subplots(figsize=(12, 8))  # Increased figure size for better readability

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    # Variables to store the average energy stored and discharged for each tariff design
    avg_energy_stored_per_shape = []
    avg_energy_discharged_per_shape = []

    for shape in shapes:
        total_energy_stored = []
        total_energy_discharged = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate total energy stored (charging) and energy discharged (discharging)
                energy_stored = df_delta[df_delta['dispatch'] < 0]['dispatch'].sum()  # Positive dispatch = charging
                energy_discharged = abs(df_delta[df_delta['dispatch'] > 0]['dispatch'].sum())  # Negative dispatch = discharging
                
                # Store the results
                total_energy_stored.append(energy_stored)
                total_energy_discharged.append(energy_discharged)

        # Convert lists to numpy arrays for easy bar plotting
        total_energy_stored = np.array(total_energy_stored)
        total_energy_discharged = np.array(total_energy_discharged)

        # Indices for the bars
        index = np.arange(len(total_energy_stored))

        # Offset for the group of bars, with spacing between scenarios
        offset = shape_idx * bar_width * 4  # Extra spacing between groups of scenarios

        # Plot bars for energy stored (charging)
        bars1 = ax.bar(index + offset, total_energy_stored, bar_width, color=colors[0], edgecolor='black',
                       label='Energy Stored' if shape_idx == 0 else "", hatch=hatches[0], alpha=alpha)

        # Plot bars for energy discharged (discharging)
        bars2 = ax.bar(index + offset + bar_width, total_energy_discharged, bar_width, color=colors[1], edgecolor='black',
                       label='Energy Discharged' if shape_idx == 0 else "", hatch=hatches[1], alpha=alpha)

        # Store average energy stored and discharged for the current tariff design
        avg_energy_stored_per_shape.append(np.mean(total_energy_stored))
        avg_energy_discharged_per_shape.append(np.mean(total_energy_discharged))

        # Add shape labels
        shapes_labels.extend([f'{shape}'])
        num_scenarios_per_shape.append(len(total_energy_stored))
        shape_idx += 1

    # Adjust tick positions and labels
    total_bars = sum(num_scenarios_per_shape)
    ticks_positions = np.arange(total_bars) * bar_width * 4 + bar_width / 2  # Add extra space between scenarios
    ax.set_xticks(ticks_positions)
    ax.set_xticklabels(shapes_labels, rotation=0, ha='right', fontsize=10)  # Increase tick label size

    ax.set_xlabel('Tariff Designs', fontsize=12)  # Increase x-axis label size
    ax.set_ylabel('Total Energy (MWh)', fontsize=12)  # Increase y-axis label size
    

    # Add trend lines
    # Convert shapes_labels to the corresponding x positions for the trend line (midpoints of the groups)
    trend_line_x_positions = np.arange(len(shapes)) * bar_width * 4 + bar_width

    # Plot trend line for energy stored
    ax.plot(trend_line_x_positions, avg_energy_stored_per_shape, marker='o', linestyle='-', color=colors[0], 
            label='Trend: Energy Stored')

    # Plot trend line for energy discharged
    ax.plot(trend_line_x_positions, avg_energy_discharged_per_shape, marker='o', linestyle='-', color=colors[1], 
            label='Trend: Energy Discharged')

    # Move the legend to the bottom, outside the plot area
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=12)
    ax.grid(False)

    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to leave space for the legend
    plt.savefig(os.path.join(output_dir_plot, "energy_comparison_with_trend.jpg"), dpi=300)
    
    
    
def plot_energy_comparison_ok(STORAGE_RESULT, params, output_dir_plot):
    alpha = 0.85
    # Get all unique shapes (tariff designs)
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4']  # Color for energy stored and energy discharged
    hatches = ['/', '\\']  # Hatching patterns
    bar_width = 0.15  # Reduced bar width for less clutter

    fig, ax = plt.subplots(figsize=(12, 8))  # Increased figure size for better readability

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    for shape in shapes:
        total_energy_stored = []
        total_energy_discharged = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate total energy stored (charging) and energy discharged (discharging)
                energy_stored = df_delta[df_delta['dispatch'] < 0]['dispatch'].sum()  # Positive dispatch = charging
                energy_discharged = abs(df_delta[df_delta['dispatch'] > 0]['dispatch'].sum())  # Negative dispatch = discharging
                
                # Store the results
                total_energy_stored.append(energy_stored)
                total_energy_discharged.append(energy_discharged)

        # Convert lists to numpy arrays for easy bar plotting
        total_energy_stored = np.array(total_energy_stored)
        total_energy_discharged = np.array(total_energy_discharged)

        # Indices for the bars
        index = np.arange(len(total_energy_stored))

        # Offset for the group of bars, with spacing between scenarios
        offset = shape_idx * bar_width * 4  # Extra spacing between groups of scenarios

        # Plot bars for energy stored (charging)
        bars1 = ax.bar(index + offset, total_energy_stored, bar_width, color=colors[0], edgecolor='black',
                       label='Energy Stored' if shape_idx == 0 else "", hatch=hatches[0], alpha=alpha)

        # Plot bars for energy discharged (discharging)
        bars2 = ax.bar(index + offset + bar_width, total_energy_discharged, bar_width, color=colors[1], edgecolor='black',
                       label='Energy Discharged' if shape_idx == 0 else "", hatch=hatches[1], alpha=alpha)

        # Add shape labels
        shapes_labels.extend([f'{shape}'])
        num_scenarios_per_shape.append(len(total_energy_stored))
        shape_idx += 1

    # Adjust tick positions and labels
    total_bars = sum(num_scenarios_per_shape)
    ticks_positions = np.arange(total_bars) * bar_width * 4 + bar_width / 2  # Add extra space between scenarios
    ax.set_xticks(ticks_positions)
    ax.set_xticklabels(shapes_labels, rotation=0, ha='right', fontsize=10)  # Increase tick label size

    ax.set_xlabel('Tariff Designs', fontsize=12)  # Increase x-axis label size
    ax.set_ylabel('Total Energy (MWh)', fontsize=12)  # Increase y-axis label size
    ax.set_title('Total Energy Stored vs. Discharged for Different Tariff Designs', fontsize=14)

    # Move the legend to the bottom, outside the plot area
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=12)

    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to leave space for the legend
    plt.savefig(os.path.join(output_dir_plot, "energy_comparison.jpg"), dpi=300)
    
    
    
def plot_revenue_comparison_02_11(STORAGE_RESULT, params, output_dir_plot):
    alpha = 0.85
    # Get all unique shapes
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4', 'grey']  # Colors for Tariff Revenue, Market Revenue, and Std Dev of Total Revenue
    bar_width = 0.2  # Adjusted for smaller bars

    fig, ax = plt.subplots(figsize=(9, 6))  # Increased figure size for better readability

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    for shape in shapes:
        average_market_revenues = []
        average_tariff_revenues = []
        average_total_revenues = []
        std_total_revenues = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate revenues
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']

                # Calculate annual revenues
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum()
                total_revenue = annual_market_revenue + annual_tariff_revenue

                # Store values
                average_market_revenues.append(annual_market_revenue.mean())
                average_tariff_revenues.append(annual_tariff_revenue.mean())
                average_total_revenues.append(total_revenue.mean())
                std_total_revenues.append(total_revenue.std())

        # Convert lists to numpy arrays
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)
        average_total_revenues = np.array(average_total_revenues)
        std_total_revenues = np.array(std_total_revenues)

        # Indices for the bars
        index = np.arange(len(average_market_revenues))
        gap = 0.1  # Gap between groups
        offset = shape_idx * (bar_width * 3 + gap)  # Added gap between groups

        # Plot stacked bars for tariff and market revenues with hatching
        bars1 = ax.bar(index + offset, average_tariff_revenues, bar_width, color=colors[0], edgecolor='black', 
                       label='Tariff-based revenue' if shape_idx == 0 else "", alpha=alpha, hatch='/')
        bars2 = ax.bar(index + offset, average_market_revenues, bar_width, bottom=average_tariff_revenues, color=colors[1], 
                       edgecolor='black', label='Energy market revenue' if shape_idx == 0 else "", alpha=alpha, hatch='\\')

        # Plot bars for standard deviation of total revenue with hatching
        bars3 = ax.bar(index + offset + bar_width, std_total_revenues, bar_width, color=colors[2], edgecolor='black', 
                       label='Std Dev of Total Revenue' if shape_idx == 0 else "", alpha=alpha, hatch='.')

        # Add annotations for revenues
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2
            ax.annotate(f'{height2:.2f}', xy=(bar2.get_x() + bar2.get_width() / 2, total_height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)
        for bar in bars3:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)

        # Add shape labels
        shapes_labels.extend([f'{shape}'])
        num_scenarios_per_shape.append(len(average_market_revenues))
        shape_idx += 1

    # Adjust tick positions and labels
    total_bars = sum(num_scenarios_per_shape)
    ticks_positions = np.arange(total_bars) * (bar_width * 3 + gap) + bar_width / 2
    ax.set_xticks(ticks_positions)
    ax.set_xticklabels(shapes_labels, rotation=0, ha='right', fontsize=10)  # Increase tick label size

    ax.set_xlabel('Shapes', fontsize=12)  # Increase x-axis label size
    ax.set_ylabel('Revenue (EUR/y)', fontsize=12)  # Increase y-axis label size
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)  # Increase legend size

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "revenue_comparison.jpg"), dpi=600)
    

def plot_revenue_comparison(STORAGE_RESULT, params, output_dir_plot):
    alpha = 0.85
    # Get all unique shapes
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4', 'grey']  # Colors for Tariff Revenue, Market Revenue, and Std Dev of Total Revenue
    bar_width = 0.2  # Adjusted for smaller bars

    fig, ax = plt.subplots(figsize=(9, 6))  # Increased figure size for better readability

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    for shape in shapes:
        average_market_revenues = []
        average_tariff_revenues = []
        average_total_revenues = []
        std_total_revenues = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate revenues
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']

                # Calculate annual revenues
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum()
                total_revenue = annual_market_revenue + annual_tariff_revenue

                # Store values
                average_market_revenues.append(annual_market_revenue.mean())
                average_tariff_revenues.append(annual_tariff_revenue.mean())
                average_total_revenues.append(total_revenue.mean())
                std_total_revenues.append(total_revenue.std())
                pass 

        # Convert lists to numpy arrays
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)
        average_total_revenues = np.array(average_total_revenues)
        std_total_revenues = np.array(std_total_revenues)

        # Indices for the bars
        index = np.arange(len(average_market_revenues))
        gap = 0.1  # Gap between groups
        offset = shape_idx * (bar_width * 3 + gap)  # Added gap between groups

        # Plot stacked bars for tariff and market revenues with hatching
        bars1 = ax.bar(index + offset, average_tariff_revenues, bar_width, color=colors[0], edgecolor='black', 
                       label='Tariff-based revenue' if shape_idx == 0 else "", alpha=alpha, hatch='/')
        bars2 = ax.bar(index + offset, average_market_revenues, bar_width, bottom=average_tariff_revenues, color=colors[1], 
                       edgecolor='black', label='Energy market revenue' if shape_idx == 0 else "", alpha=alpha, hatch='\\')

        # Plot bars for standard deviation of total revenue with hatching
        bars3 = ax.bar(index + offset + bar_width, std_total_revenues, bar_width, color=colors[2], edgecolor='black', 
                       label='Std Dev of Total Revenue' if shape_idx == 0 else "", alpha=alpha, hatch='.')

        # Add annotations for revenues
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:,.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2
            ax.annotate(f'{height2:,.2f}', xy=(bar2.get_x() + bar2.get_width() / 2, total_height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)
        for bar in bars3:
            height = bar.get_height()
            ax.annotate(f'{height:,.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)

        # Add shape labels
        shapes_labels.extend([f'{shape}'])
        num_scenarios_per_shape.append(len(average_market_revenues))
        shape_idx += 1

    # Adjust tick positions and labels
    total_bars = sum(num_scenarios_per_shape)
    ticks_positions = np.arange(total_bars) * (bar_width * 3 + gap) + bar_width / 2
    ax.set_xticks(ticks_positions)
    ax.set_xticklabels(shapes_labels, rotation=0, ha='right', fontsize=10)  # Increase tick label size

    ax.set_xlabel('Shapes', fontsize=12)  # Increase x-axis label size
    ax.set_ylabel('Revenue (EUR/y)', fontsize=12)  # Increase y-axis label size
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)  # Increase legend size

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "revenue_comparison.jpg"), dpi=600)
    


def plot_revenue_by_year(STORAGE_RESULT, params, output_dir_plot): #TO BE INCLUDED TO ANSWER REVIEWER COMMENT 12. 
    alpha = 0.85
    # Get all unique shapes
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4', 'grey']  # Colors for Tariff Revenue, Market Revenue, and Std Dev of Total Revenue
    bar_width = 0.2  # Adjusted for smaller bars

    fig, axes = plt.subplots(2, 2, figsize=(12, 12))  # 2x2 grid for subplots

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    for i, shape in enumerate(shapes):
        ax = axes[i // 2, i % 2]  # Select the correct subplot axis

        annual_market_revenue_all = []
        annual_tariff_revenue_all = []
        total_revenue_all = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate revenues
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']

                # Calculate annual revenues
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum()
                total_revenue = annual_market_revenue + annual_tariff_revenue

                # Store values
                annual_market_revenue_all.append(annual_market_revenue)
                annual_tariff_revenue_all.append(annual_tariff_revenue)
                total_revenue_all.append(total_revenue)

        # Combine all years data into one series for each shape
        all_years = np.unique(np.concatenate([revenue.index for revenue in total_revenue_all]))  # All years across all scenarios
        avg_revenue = np.mean([revenue.mean() for revenue in total_revenue_all], axis=0)  # Mean across scenarios

        # Plot total revenue per year
        total_revenue_mean_per_year = [np.mean([revenue.get(year, 0) for revenue in total_revenue_all]) for year in all_years]
        ax.bar(all_years, total_revenue_mean_per_year, width=0.8, color=colors[2], edgecolor='black', alpha=alpha)

        # Annotate the bars with average revenue
        for year, value in zip(all_years, total_revenue_mean_per_year):
            ax.annotate(f'{value:,.2f}', xy=(year, value), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

        # Plot the average total revenue line
        ax.axhline(y=avg_revenue, color='r', linestyle='--', label=f'Mean Total Revenue: {avg_revenue:,.2f}')

        # Set labels and title
        ax.set_title(f'Total Revenue Evolution by Year for Shape {shape}', fontsize=12)
        ax.set_xlabel('Year', fontsize=10)
        ax.set_ylabel('Revenue (EUR)', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)

        # Store shape labels
        shapes_labels.append(f'{shape}')
        num_scenarios_per_shape.append(len(total_revenue_all))

    # Adjust subplot layout
    plt.tight_layout()

    # Save plot
    plt.savefig(os.path.join(output_dir_plot, "revenue_evolution_by_year.jpg"), dpi=600)


    

def plot_revenue_comparison_NEW(STORAGE_RESULT, params, output_dir_plot):
    alpha = 0.85
    # Get all unique shapes
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4', 'grey']  # Colors for Tariff Revenue, Market Revenue, and Std Dev of Total Revenue
    bar_width = 0.2  # Adjusted for smaller bars

    fig, ax = plt.subplots(figsize=(9, 6))  # Increased figure size for better readability

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    for shape in shapes:
        average_market_revenues = []
        average_tariff_revenues = []
        average_total_revenues = []
        std_total_revenues = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate revenues
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']

                # Calculate annual revenues
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum()
                total_revenue = annual_market_revenue + annual_tariff_revenue

                # Store values
                average_market_revenues.append(annual_market_revenue.mean())
                average_tariff_revenues.append(annual_tariff_revenue.mean())
                average_total_revenues.append(total_revenue.mean())
                std_total_revenues.append(total_revenue.std())

        # Convert lists to numpy arrays
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)
        average_total_revenues = np.array(average_total_revenues)
        std_total_revenues = np.array(std_total_revenues)

        # Indices for the bars
        index = np.arange(len(average_market_revenues))
        gap = 0.1  # Gap between groups
        offset = shape_idx * (bar_width * 3 + gap)  # Added gap between groups

        # Plot stacked bars for tariff and market revenues with hatching
        bars1 = ax.bar(index + offset, average_tariff_revenues, bar_width, color=colors[0], edgecolor='black', 
                       label='Tariff-based revenue' if shape_idx == 0 else "", alpha=alpha, hatch='/')
        bars2 = ax.bar(index + offset, average_market_revenues, bar_width, bottom=average_tariff_revenues, color=colors[1], 
                       edgecolor='black', label='Energy market revenue' if shape_idx == 0 else "", alpha=alpha, hatch='\\')

        # Plot bars for standard deviation of total revenue with hatching
        bars3 = ax.bar(index + offset + bar_width, std_total_revenues, bar_width, color=colors[2], edgecolor='black', 
                       label='Std Dev of Total Revenue' if shape_idx == 0 else "", alpha=alpha, hatch='.')

        # Add annotations for revenues
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:,.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2
            ax.annotate(f'{height2:,.2f}', xy=(bar2.get_x() + bar2.get_width() / 2, total_height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)
        for bar in bars3:
            height = bar.get_height()
            ax.annotate(f'{height:,.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)

        # Add shape labels
        shapes_labels.extend([f'{shape}'])
        num_scenarios_per_shape.append(len(average_market_revenues))
        shape_idx += 1

    # Adjust tick positions and labels
    total_bars = sum(num_scenarios_per_shape)
    ticks_positions = np.arange(total_bars) * (bar_width * 3 + gap) + bar_width / 2
    ax.set_xticks(ticks_positions)
    ax.set_xticklabels(shapes_labels, rotation=0, ha='right', fontsize=10)  # Increase tick label size

    ax.set_xlabel('Shapes', fontsize=12)  # Increase x-axis label size
    ax.set_ylabel('Revenue (EUR/y)', fontsize=12)  # Increase y-axis label size
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)  # Increase legend size

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "revenue_comparison.jpg"), dpi=600)


def plot_revenue_variability(STORAGE_RESULT, params, output_dir_plot):
    # Setup
    alpha = 0.85
    colors = ['#ff7f0e', '#1f77b4']  # Colors for Tariff Revenue and Market Revenue
    bar_width = 0.3

    # Create a figure for the plot
    fig, ax = plt.subplots(figsize=(9, 6))

    # Iterate through all the shapes (scenarios) and compute the yearly variance in revenues
    for shape in sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys())):
        years = []
        variance_market_revenues = []
        variance_tariff_revenues = []
        
        # Iterate over each scenario to calculate variances
        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate revenues
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']

                # Group by year and calculate the variance of revenues per year
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum()
                
                # Store the variance of revenues for market and tariff-based revenues
                variance_market_revenues.append(annual_market_revenue.var())
                variance_tariff_revenues.append(annual_tariff_revenue.var())
                years = list(annual_market_revenue.index)  # Assuming same years for all scenarios

        # Convert to numpy arrays for plotting
        variance_market_revenues = np.array(variance_market_revenues)
        variance_tariff_revenues = np.array(variance_tariff_revenues)

        # Plot the variance for both types of revenues (market and tariff-based)
        ax.plot(years, variance_market_revenues, label=f'Variance of Market Revenue ({shape})', color=colors[1], marker='o')
        ax.plot(years, variance_tariff_revenues, label=f'Variance of Tariff Revenue ({shape})', color=colors[0], marker='x')

    # Set up labels and title
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Revenue Variance (EUR^2)', fontsize=12)
    ax.set_title('Yearly Variability in Market and Tariff Revenue', fontsize=14)
    ax.legend(loc='upper left', fontsize=10)

    # Adjust layout for better readability
    plt.tight_layout()

    # Save the plot
    plt.savefig(os.path.join(output_dir_plot, "revenue_variability.jpg"), dpi=600)

    # Show the plot
    plt.show()



def plot_revenue_comparison_ok3(STORAGE_RESULT, params, output_dir_plot):
    import matplotlib.pyplot as plt
    import numpy as np
    import os

    alpha = 0.85
    hatch_patterns = ['/', '\\', 'x']  # Hatching patterns for different bar categories
    # Get all unique shapes
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#ff7f0e', '#1f77b4', 'grey']  # Colors for Tariff Revenue, Market Revenue, and Std Dev of Total Revenue
    bar_width = 0.3

    fig, ax = plt.subplots(figsize=(9, 7))

    shape_idx = 0
    shapes_labels = []  # To store shape labels
    num_scenarios_per_shape = []  # To store number of scenarios per shape

    for shape in shapes:
        average_market_revenues = []
        average_tariff_revenues = []
        average_total_revenues = []
        std_total_revenues = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculate revenues
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']

                # Calculate annual revenues
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum()
                total_revenue = annual_market_revenue + annual_tariff_revenue

                # Store values
                average_market_revenues.append(annual_market_revenue.mean())
                average_tariff_revenues.append(annual_tariff_revenue.mean())
                average_total_revenues.append(total_revenue.mean())
                std_total_revenues.append(total_revenue.std())

        # Convert lists to numpy arrays
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)
        average_total_revenues = np.array(average_total_revenues)
        std_total_revenues = np.array(std_total_revenues)

        # Indices for the bars
        index = np.arange(len(average_market_revenues))

        # Offset for the group of bars
        offset = shape_idx * bar_width * 3  # Increased gap between groups

        # Plot stacked bars for tariff and market revenues
        bars1 = ax.bar(index + offset, average_tariff_revenues, bar_width, color=colors[0], edgecolor='black', 
                       hatch=hatch_patterns[0], label='Tariff Revenue' if shape_idx == 0 else "", alpha=alpha)
        bars2 = ax.bar(index + offset, average_market_revenues, bar_width, bottom=average_tariff_revenues, 
                       color=colors[1], edgecolor='black', hatch=hatch_patterns[1], label='Market Revenue' if shape_idx == 0 else "", alpha=alpha)

        # Plot bars for standard deviation of total revenue
        bars3 = ax.bar(index + offset + bar_width, std_total_revenues, bar_width, color=colors[2], edgecolor='black', 
                       hatch=hatch_patterns[2], label='Std Dev of Total Revenue' if shape_idx == 0 else "", alpha=alpha)

        # Add annotations for tariff, market, and standard deviation revenues
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", 
                        ha='center', va='bottom', fontsize=8)
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2
            ax.annotate(f'{height2:.2f}', xy=(bar2.get_x() + bar2.get_width() / 2, total_height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)
        for bar in bars3:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), 
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)

        # Add shape labels
        shapes_labels.extend([f'{shape}'])
        num_scenarios_per_shape.append(len(average_market_revenues))
        shape_idx += 1

    # Adjust tick positions and labels
    total_bars = sum(num_scenarios_per_shape)
    ticks_positions = np.arange(total_bars) * bar_width * 3 + bar_width / 2  # Adjusting tick positions for wider spacing
    ax.set_xticks(ticks_positions)
    ax.set_xticklabels(shapes_labels, rotation=0, ha='right', fontsize=10)

    ax.set_xlabel('Shapes', fontsize=10)
    ax.set_ylabel('Revenue (EUR/y)', fontsize=10)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "revenue_comparison.jpg"), dpi=600)

    
def plot_tariff_revenue_comparison(STORAGE_RESULT, params, output_dir_plot):
    
    # Obtenir toutes les formes uniques sauf "without_tariff"
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    shapes = [shape for shape in shapes if shape != "without_tariff"]  # Exclure "without_tariff"
    colors = ['#ff7f0e']  # Couleur pour Tariff Revenue
    hatches = ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']  # Différents types de hachures
    bar_width = 0.2

    # Définir le nombre de sous-graphiques
    num_shapes = len(shapes)
    fig, axes = plt.subplots(1, num_shapes, figsize=(4 * num_shapes, 5), sharey=True)

    # Assurer que axes est toujours une liste même si n == 1
    if num_shapes == 1:
        axes = [axes]

    for shape_idx, shape in enumerate(shapes):
        ax = axes[shape_idx]
        annual_tariff_revenues = []
        years = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculer les revenus tarifaires annuels
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
                annual_revenue = df_delta.groupby('year')['revenue_tariff'].sum()

                # Ajouter les revenus et les années
                annual_tariff_revenues.extend(annual_revenue)
                years.extend(annual_revenue.index)

        # Convertir les listes en arrays numpy
        annual_tariff_revenues = np.array(annual_tariff_revenues)
        years = np.array(years)

        # Indices pour les barres
        index = np.arange(len(years))

        # Tracer les barres
        ax.bar(index, annual_tariff_revenues, bar_width, color=colors[0], edgecolor='black', hatch=hatches[shape_idx % len(hatches)], label='Tariff Revenue')

        # Ajouter les labels pour les années
        ax.set_xticks(index)
        ax.set_xticklabels(years, rotation=90, ha='right', fontsize=12)  # Augmenter la taille des labels des ticks
        ax.set_title(f'{shape}', fontsize=14)  # Augmenter la taille du titre

    fig.supxlabel('Years', fontsize=16)  # Augmenter la taille de l'étiquette de l'axe x
    fig.supylabel('Tariff Revenue (EUR)', fontsize=16)  # Augmenter la taille de l'étiquette de l'axe y

    # Ajouter une légende commune en bas de la figure
    handles, labels = ax.get_legend_handles_labels()
    #fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=1, fontsize=12)  # Augmenter la taille de la légende


    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "revenue_tariff_comparison.png"), dpi=600)
    
    return None



def plot_storage_revenues(STORAGE_RESULT, params, categories, output_dir_plot):
    
    fig, axes = plt.subplots(3, 3, figsize=(15, 15))

    bar_width = 0.25
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

    for idx, (scenario, df_delta) in enumerate(STORAGE_RESULT.items()):
        # Calculer les revenus
        df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
        df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
        df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
        
        annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
        annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()
        annual_total_revenue = df_delta.groupby('year')['revenue_net'].sum().tolist()
        
        # Calculer les revenus annuels moyens
        average_market_revenue = np.mean(annual_market_revenue)
        average_tariff_revenue = np.mean(annual_tariff_revenue)
        average_total_revenue = np.mean(annual_total_revenue)

        # Lire le delta
        delta = float(params[scenario]['global']['tariff']['delta'])
        
        # Préparer les données pour les bar charts
        revenues = [average_market_revenue, average_tariff_revenue, average_total_revenue]
        
        # Calculer les pourcentages par rapport au revenu total
        market_percentage = (average_market_revenue / average_total_revenue) * 100
        tariff_percentage = (average_tariff_revenue / average_total_revenue) * 100
        
        # Obtenir l'axe pour le subplot actuel
        ax = axes[idx // 3, idx % 3]
        
        # Tracer les bar charts sans hachures mais avec des bordures noires
        bars = []
        for i, (revenue, color) in enumerate(zip(revenues, colors)):
            bar = ax.bar(i, revenue, bar_width, color=color, edgecolor='black')
            bars.append(bar)
        
        # Ajouter le titre avec le delta
        ax.set_title(f'Δ: {delta:.2f}')
        ax.set_xticks(np.arange(len(categories)))
        ax.set_xticklabels(categories, rotation=0, ha='right')
        
        # Annoter chaque barre avec sa valeur ou le pourcentage
        for i, bar in enumerate(bars):
            for rect in bar:
                height = rect.get_height()
                if i == 0:  # market revenue
                    annotation = f'{market_percentage:.2f}%'
                elif i == 1:  # tariff revenue
                    annotation = f'{tariff_percentage:.2f}%'
                else:  # total revenue
                    annotation = ''
                ax.annotate(annotation, 
                            xy=(rect.get_x() + rect.get_width() / 2, height), 
                            xytext=(0, 3), 
                            textcoords='offset points', 
                            ha='center', 
                            fontsize=8)
        
        # Afficher les labels des axes x et y uniquement pour les subplots en bas et à gauche
        if idx // 3 == 2:
            ax.set_xlabel('Revenue Types')
        if idx % 3 == 0:
            ax.set_ylabel('Average Revenue (EUR/y)')
        
        ax.grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Sensitivity_on_delta.png"), dpi=400)
    return None


def plot_stacked_revenues(STORAGE_RESULT, params, output_dir_plot):
    deltas = []
    average_market_revenues = []
    average_tariff_revenues = []
    average_total_revenues = []

    for scenario, df_delta in STORAGE_RESULT.items():
        # Calculer les revenus
        df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
        df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
        df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
        
        # Calculer les revenus moyens
        annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
        annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()
        annual_total_revenue = df_delta.groupby('year')['revenue_net'].sum().tolist()
        
        # Calculer les revenus annuels moyens
        average_market_revenue = np.mean(annual_market_revenue)
        average_tariff_revenue = np.mean(annual_tariff_revenue)
        average_total_revenue = np.mean(annual_total_revenue)

        # Lire le delta
        delta = float(params[scenario]['global']['tariff']['delta'])
        
        # Stocker les valeurs
        deltas.append(delta)
        average_market_revenues.append(average_market_revenue)
        average_tariff_revenues.append(average_tariff_revenue)
        average_total_revenues.append(average_total_revenue)

    # Tracer le bar chart empilé
    fig, ax = plt.subplots(figsize=(12, 8))

    bar_width = 0.35
    index = np.arange(len(deltas))
    
    bars1 = ax.bar(index, average_market_revenues, bar_width, label='Market Revenue', color='#1f77b4', hatch='/')
    bars2 = ax.bar(index, average_tariff_revenues, bar_width, bottom=average_market_revenues, label='Tariff Revenue', color='#ff7f0e', hatch='\\')
    bars3 = ax.bar(index, average_total_revenues, bar_width, bottom=np.array(average_market_revenues) + np.array(average_tariff_revenues), label='Total Revenue', color='#2ca02c', hatch='x')

    ax.set_xlabel('Δ')
    ax.set_ylabel('Average Revenue (EUR/y)')
    #ax.set_title('Average Revenue by Delta')
    ax.set_xticks(index)
    ax.set_xticklabels([f'{delta:.2f}' for delta in deltas])
    ax.legend()

    # Annoter chaque barre avec sa valeur
    def annotate_bars(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}', 
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_y() + height / 2), 
                        xytext=(0, 3), 
                        textcoords='offset points', 
                        ha='center', 
                        fontsize=8)

    annotate_bars(bars1)
    annotate_bars(bars2)
    annotate_bars(bars3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Sensitivity_on_delta_stacked.png"), dpi=350)
    return None 


def plot_stacked_revenues_2(STORAGE_RESULT, params, output_dir_plot):
    deltas = []
    average_market_revenues = []
    average_tariff_revenues = []

    for scenario, df_delta in STORAGE_RESULT.items():
        # Calculer les revenus
        df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
        df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
        df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
        
        # Calculer les revenus annuels moyens
        annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
        annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()
        
        # Calculer les revenus moyens
        average_market_revenue = np.mean(annual_market_revenue)
        average_tariff_revenue = np.mean(annual_tariff_revenue)

        # Lire le delta
        delta = float(params[scenario]['global']['tariff']['delta'])
        
        # Stocker les valeurs
        deltas.append(delta)
        average_market_revenues.append(average_market_revenue)
        average_tariff_revenues.append(average_tariff_revenue)

    # Tracer le bar chart empilé
    fig, ax = plt.subplots(figsize=(12, 8))

    bar_width = 0.35
    index = np.arange(len(deltas))
    
    bars1 = ax.bar(index, average_market_revenues, bar_width, label='Market Revenue', color='#1f77b4')
    bars2 = ax.bar(index, average_tariff_revenues, bar_width, bottom=average_market_revenues, label='Tariff Revenue', color='#ff7f0e')

    ax.set_xlabel('Δ')
    ax.set_ylabel('Average Revenue (EUR/y)')
    ax.set_xticks(index)
    ax.set_xticklabels([f'{delta:.2f}' for delta in deltas])
    ax.legend()

    # Annoter chaque barre avec sa valeur au milieu des barres
    def annotate_bars(bars, revenues):
        for bar, revenue in zip(bars, revenues):
            height = bar.get_height()
            ax.annotate(f'{height:.2f}', 
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_y() + height / 2), 
                        xytext=(0, 0), 
                        textcoords='offset points', 
                        ha='center', 
                        va='center', 
                        color='white',
                        fontsize=8,
                        rotation=90)

    annotate_bars(bars1, average_market_revenues)
    annotate_bars(bars2, average_tariff_revenues)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Sensitivity_on_delta_stacked_2.png"), dpi=350)
    return None



def plot_stacked_revenues_3_old(STORAGE_RESULT, params, output_dir_plot):
    deltas = []
    average_market_revenues = []
    average_tariff_revenues = []
    std_total_revenues = []

    for scenario, df_delta in STORAGE_RESULT.items():
        # Calculer les revenus
        df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
        df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
        df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
        
        # Calculer les revenus annuels moyens
        annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
        annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()
        annual_total_revenue = [m + t for m, t in zip(annual_market_revenue, annual_tariff_revenue)]
        
        # Calculer les revenus moyens
        average_market_revenue = np.mean(annual_market_revenue)
        average_tariff_revenue = np.mean(annual_tariff_revenue)
        
        # Calculer la déviation standard des revenus annuels totaux
        std_total_revenue = np.std(annual_total_revenue)

        # Lire le delta
        delta = float(params[scenario]['global']['tariff']['delta'])
        
        # Stocker les valeurs
        deltas.append(delta)
        average_market_revenues.append(average_market_revenue)
        average_tariff_revenues.append(average_tariff_revenue)
        std_total_revenues.append(std_total_revenue)

    # Tracer le bar chart empilé
    fig, ax1 = plt.subplots(figsize=(12, 6))

    bar_width = 0.35
    index = np.arange(len(deltas))
    
    bars1 = ax1.bar(index, average_market_revenues, bar_width, label='Energy market revenue', color='#1f77b4', edgecolor='black')
    bars2 = ax1.bar(index, average_tariff_revenues, bar_width, bottom=average_market_revenues, label='Tariff-based Revenue', color='#ff7f0e', edgecolor='black')

    ax1.set_xlabel('Δ', fontsize=16)
    ax1.set_ylabel('Average Revenue (EUR/y)', fontsize=14)
    ax1.set_xticks(index)
    ax1.set_xticklabels([f'{delta:.2f}' for delta in deltas], fontsize=14)

    # Ajouter un deuxième axe pour la déviation standard des revenus annuels totaux
    ax2 = ax1.twinx()
    bars3 = ax2.bar(index + bar_width, std_total_revenues, bar_width, label='Std Dev of Total Revenue', color='grey', edgecolor='black', alpha=0.7)

    ax2.set_ylabel('Std Dev of Total Revenue (EUR/y)', fontsize=14)

    # Déplacer la légende en bas, en dehors du graphique
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=12)

    # Annoter chaque barre avec le pourcentage de sa valeur par rapport à la somme des valeurs des barres empilées
    def annotate_bars(bars, revenues, total_revenues):
        for bar, revenue, total_revenue in zip(bars, revenues, total_revenues):
            percentage = (revenue / total_revenue) * 100
            ax1.annotate(f'{percentage:.2f}%', 
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_y() + bar.get_height() / 2), 
                        xytext=(0, 0), 
                        textcoords='offset points', 
                        ha='center', 
                        va='center', 
                        color='white',
                        fontsize=10,
                        rotation=90)

    total_revenues = np.array(average_market_revenues) + np.array(average_tariff_revenues)
    annotate_bars(bars1, average_market_revenues, total_revenues)
    annotate_bars(bars2, average_tariff_revenues, total_revenues)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Sensitivity_on_delta_stacked_3.png"), dpi=350)
    
def plot_stacked_revenues_3(STORAGE_RESULT, params, output_dir_plot):
    deltas = []
    average_market_revenues = []
    average_tariff_revenues = []

    for scenario, df_delta in STORAGE_RESULT.items():
        # Calculer les revenus
        df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
        df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
        df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']
        
        # Calculer les revenus annuels moyens
        annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
        annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()
        
        # Calculer les revenus moyens
        average_market_revenue = np.mean(annual_market_revenue)
        average_tariff_revenue = np.mean(annual_tariff_revenue)
        
        # Lire le delta
        delta = float(params[scenario]['global']['tariff']['delta'])
        
        # Stocker les valeurs
        deltas.append(delta)
        average_market_revenues.append(average_market_revenue)
        average_tariff_revenues.append(average_tariff_revenue)

    # Tracer le bar chart empilé
    fig, ax1 = plt.subplots(figsize=(12, 6))

    bar_width = 0.35
    index = np.arange(len(deltas))
    
    bars1 = ax1.bar(index, average_market_revenues, bar_width, label='Energy market revenue', color='#1f77b4', edgecolor='black')
    bars2 = ax1.bar(index, average_tariff_revenues, bar_width, bottom=average_market_revenues, label='Tariff-based Revenue', color='#ff7f0e', edgecolor='black')

    ax1.set_xlabel('Δ', fontsize=16)
    ax1.set_ylabel('Average Revenue (EUR/y)', fontsize=14)
    ax1.set_xticks(index)
    ax1.set_xticklabels([f'{delta:.2f}' for delta in deltas], fontsize=14)
    
    # Déplacer la légende en bas, en dehors du graphique
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=12)

    # Annoter chaque barre avec le pourcentage de sa valeur par rapport à la somme des valeurs des barres empilées
    def annotate_bars(bars, revenues, total_revenues):
        for bar, revenue, total_revenue in zip(bars, revenues, total_revenues):
            percentage = (revenue / total_revenue) * 100
            ax1.annotate(f'{percentage:.2f}%', 
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_y() + bar.get_height() / 2), 
                        xytext=(0, 0), 
                        textcoords='offset points', 
                        ha='center', 
                        va='center', 
                        color='white',
                        fontsize=10,
                        rotation=90)

    total_revenues = np.array(average_market_revenues) + np.array(average_tariff_revenues)
    annotate_bars(bars1, average_market_revenues, total_revenues)
    annotate_bars(bars2, average_tariff_revenues, total_revenues)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Sensitivity_on_delta_stacked_3.png"), dpi=350)

    
    
    
def plot_stacked_revenues_by_shape(STORAGE_RESULT, params, output_dir_plot):
    # Obtenir toutes les formes uniques
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#1f77b4', '#ff7f0e']  # Couleurs pour Market Revenue et Tariff Revenue
    hatches = ['/', '\\']
    bar_width=0.4

    fig, axes = plt.subplots(len(shapes), 1, figsize=(12, 8 * len(shapes)))

    if len(shapes) == 1:
        axes = [axes]  # S'assurer que axes soit toujours une liste

    for shape_idx, shape in enumerate(shapes):
        shares = []
        average_market_revenues = []
        average_tariff_revenues = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculer les revenus
                df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']

                # Calculer les revenus annuels moyens
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()
                
                # Calculer les revenus moyens
                average_market_revenue = np.mean(annual_market_revenue)
                average_tariff_revenue = np.mean(annual_tariff_revenue)

                # Lire le share
                share = float(params[scenario]['global']['tariff']['share'])
                
                # Stocker les valeurs
                shares.append(share)
                average_market_revenues.append(average_market_revenue)
                average_tariff_revenues.append(average_tariff_revenue)

        # Convertir les listes en arrays numpy
        shares = np.array(shares)
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)

        # Tracer les bar charts pour la forme actuelle
        ax = axes[shape_idx]
        index = np.arange(len(shares))
        
        bars1 = ax.bar(index, average_market_revenues, bar_width, label='Market Revenue', color=colors[0], hatch=hatches[0])
        bars2 = ax.bar(index, average_tariff_revenues, bar_width, bottom=average_market_revenues, label='Tariff Revenue', color=colors[1], hatch=hatches[1])

        # Ajouter les annotations
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2
            ax.annotate(f'{total_height:.2f}', 
                        xy=(bar1.get_x() + bar1.get_width() / 2, total_height), 
                        xytext=(0, 3), 
                        textcoords='offset points', 
                        ha='center', 
                        fontsize=8)

        ax.set_xlabel('share')
        ax.set_ylabel('Average Revenue (EUR/y)')
        ax.set_title(f'{shape} tariff')
        ax.set_xticks(index)
        ax.set_xticklabels([f'{share:.2f}' for share in shares])
        ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Sensitivity_on_share_and_shape_stacked.png"), dpi=350)
    
    return None


def plot_stacked_revenues_by_shape_horizontal(STORAGE_RESULT, params, output_dir_plot):
    # Obtenir toutes les formes uniques
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#1f77b4', '#ff7f0e']  # Couleurs pour Market Revenue et Tariff Revenue
    hatches = ['/', '\\']
    bar_width = 0.3

    # Modifier les subplots pour qu'ils soient horizontaux
    fig, axes = plt.subplots(1, len(shapes), figsize=(7 * len(shapes), 5))

    if len(shapes) == 1:
        axes = [axes]  # S'assurer que axes soit toujours une liste

    for shape_idx, shape in enumerate(shapes):
        shares = []
        average_market_revenues = []
        average_tariff_revenues = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculer les revenus
                df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']

                # Calculer les revenus annuels moyens
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()
                
                # Calculer les revenus moyens
                average_market_revenue = np.mean(annual_market_revenue)
                average_tariff_revenue = np.mean(annual_tariff_revenue)

                # Lire le share
                share = float(params[scenario]['global']['tariff']['share'])
                
                # Stocker les valeurs
                shares.append(share)
                average_market_revenues.append(average_market_revenue)
                average_tariff_revenues.append(average_tariff_revenue)

        # Convertir les listes en arrays numpy
        shares = np.array(shares)
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)

        # Tracer les bar charts pour la forme actuelle
        ax = axes[shape_idx]
        index = np.arange(len(shares))
        
        bars1 = ax.bar(index, average_market_revenues, bar_width, label='Market Revenue', color=colors[0], hatch=hatches[0])
        bars2 = ax.bar(index, average_tariff_revenues, bar_width, bottom=average_market_revenues, label='Tariff Revenue', color=colors[1], hatch=hatches[1])

        # Ajouter les annotations
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2

            # Ajouter l'annotation pour le total
            ax.annotate(f'{total_height:.2f}', 
                        xy=(bar1.get_x() + bar1.get_width() / 2, total_height), 
                        xytext=(0, 3), 
                        textcoords='offset points', 
                        ha='center', 
                        fontsize=10)

            # Ajouter les annotations pour les pourcentages
            market_pct = (height1 / total_height) * 100 if total_height > 0 else 0
            tariff_pct = (height2 / total_height) * 100 if total_height > 0 else 0

            ax.annotate(f'{market_pct:.1f}%', 
                        xy=(bar1.get_x() + bar1.get_width() / 2, height1 / 2), 
                        xytext=(0, 0), 
                        textcoords='offset points', 
                        ha='center', 
                        color='white',
                        fontsize=10)
            
            ax.annotate(f'{tariff_pct:.1f}%', 
                        xy=(bar2.get_x() + bar2.get_width() / 2, height1 + height2 / 2), 
                        xytext=(0, 0), 
                        textcoords='offset points', 
                        ha='center', 
                        color='white',
                        fontsize=10)

        ax.set_xlabel('share')
        ax.set_ylabel('Average Revenue (EUR/y)')
        ax.set_title(f'{shape} Tariff')
        ax.set_xticks(index)
        ax.set_xticklabels([f'{share:.2f}' for share in shares])
        ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Sensitivity_on_share_and_shape_stacked_horizontal.png"), dpi=400)
    
    return None


def plot_stacked_revenues_by_shape_vertical_OK(STORAGE_RESULT, params, output_dir_plot):
    # Obtenir toutes les formes uniques
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#1f77b4', '#ff7f0e']  # Couleurs pour Market Revenue et Tariff Revenue
    bar_width = 0.4

    fig, axes = plt.subplots(len(shapes), 1, figsize=(6, 4 * len(shapes)))

    if len(shapes) == 1:
        axes = [axes]  # S'assurer que axes soit toujours une liste

    for shape_idx, shape in enumerate(shapes):
        shares = []
        average_market_revenues = []
        average_tariff_revenues = []

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculer les revenus
                df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']

                # Calculer les revenus annuels moyens
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()
                
                # Calculer les revenus moyens
                average_market_revenue = np.mean(annual_market_revenue)
                average_tariff_revenue = np.mean(annual_tariff_revenue)

                # Lire le share
                share = float(params[scenario]['global']['tariff']['share'])
                
                # Stocker les valeurs
                shares.append(share)
                average_market_revenues.append(average_market_revenue)
                average_tariff_revenues.append(average_tariff_revenue)

        # Convertir les listes en arrays numpy
        shares = np.array(shares)
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)

        # Tracer les bar charts pour la forme actuelle
        ax = axes[shape_idx]
        index = np.arange(len(shares))
        
        bars1 = ax.bar(index, average_market_revenues, bar_width, label='Market Revenue', color=colors[0], edgecolor='black')
        bars2 = ax.bar(index, average_tariff_revenues, bar_width, bottom=average_market_revenues, label='Tariff Revenue', color=colors[1], edgecolor='black')

        # Ajouter les annotations pour les pourcentages
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2

            if total_height > 0:
                market_pct = (height1 / total_height) * 100
                tariff_pct = (height2 / total_height) * 100

                # Ajuster les pourcentages pour qu'ils ne dépassent pas 100%
                market_pct = min(market_pct, 100)
                tariff_pct = min(tariff_pct, 100 - market_pct)

                ax.annotate(f'{market_pct:.1f}%', 
                            xy=(bar1.get_x() + bar1.get_width() / 2, height1 / 2), 
                            xytext=(0, 0), 
                            textcoords='offset points', 
                            ha='center', 
                            color='white',
                            fontsize=7)
                
                ax.annotate(f'{tariff_pct:.1f}%', 
                            xy=(bar2.get_x() + bar2.get_width() / 2, height1 + height2 / 2), 
                            xytext=(0, 0), 
                            textcoords='offset points', 
                            ha='center', 
                            color='black',
                            rotation='vertical',
                            fontsize=7)

        ax.set_xlabel('share')
        ax.set_ylabel('Average Revenue (EUR/y)')
        ax.set_title(f'{shape}')
        ax.set_xticks(index)
        ax.set_xticklabels([f'{share:.2f}' for share in shares])
        ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "Sensitivity_on_share_and_shape_stacked_vertical.png"), dpi=400)
    plt.close(fig)
    return None

def plot_stacked_revenues_by_shape_vertical(STORAGE_RESULT, params, output_dir_plot):
    # Obtenir toutes les formes uniques
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#1f77b4', '#ff7f0e']  # Couleurs pour Market Revenue et Tariff Revenue
    bar_width = 0.45

    for shape in shapes:
        # Initialiser les listes pour chaque forme
        shares = []
        average_market_revenues = []
        average_tariff_revenues = []

        # Créer une nouvelle figure pour chaque forme
        fig, ax = plt.subplots(figsize=(6, 6))

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculer les revenus
                df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']

                # Calculer les revenus annuels moyens
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()

                # Calculer les revenus moyens
                average_market_revenue = np.mean(annual_market_revenue)
                average_tariff_revenue = np.mean(annual_tariff_revenue)

                # Lire le share
                share = float(params[scenario]['global']['tariff']['share'])

                # Stocker les valeurs
                shares.append(share)
                average_market_revenues.append(average_market_revenue)
                average_tariff_revenues.append(average_tariff_revenue)

        # Convertir les listes en arrays numpy
        shares = np.array(shares)
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)

        # Tracer les bar charts pour la forme actuelle
        index = np.arange(len(shares))
        
        bars1 = ax.bar(index, average_market_revenues, bar_width, label='Market Revenue', color=colors[0], edgecolor='black')
        bars2 = ax.bar(index, average_tariff_revenues, bar_width, bottom=average_market_revenues, label='Tariff Revenue', color=colors[1], edgecolor='black')

        # Ajouter les annotations pour les pourcentages
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2

            if total_height > 0:
                market_pct = (height1 / total_height) * 100
                tariff_pct = (height2 / total_height) * 100

                # Ajuster les pourcentages pour qu'ils ne dépassent pas 100%
                #market_pct = min(market_pct, 100)
                #tariff_pct = min(tariff_pct, 100 - market_pct)

                ax.annotate(f'{market_pct:.1f}%', 
                            xy=(bar1.get_x() + bar1.get_width() / 2, height1 / 2), 
                            xytext=(0, 0), 
                            textcoords='offset points', 
                            ha='center', 
                            color='white',
                            fontsize=7)

                ax.annotate(f'{tariff_pct:.1f}%', 
                            xy=(bar2.get_x() + bar2.get_width() / 2, height1 + height2 / 2), 
                            xytext=(0, 0), 
                            textcoords='offset points', 
                            ha='center', 
                            color='black',
                            rotation='vertical',
                            fontsize=7)

        ax.set_xlabel('share')
        ax.set_ylabel('Average Revenue (EUR/y)')
        ax.set_title(f'{shape}')
        ax.set_xticks(index)
        ax.set_xticklabels([f'{share:.2f}' for share in shares])

        # Ajuster la limite supérieure de l'axe y pour ajouter de l'espace au-dessus des barres
        max_height = (average_market_revenues + average_tariff_revenues).max()
        ax.set_ylim(0, max_height * 1.1)  # Ajouter 10% d'espace au-dessus

        # Créer une seule légende sous chaque figure
        ax.legend([bars1, bars2], labels=['Energy market revenue', 'Tariff-based revenue'], loc='lower center', ncol=2, bbox_to_anchor=(0.5, -0.3))

        # Ajuster la place en bas pour la légende
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.2)  # Ajuster pour ne pas superposer la légende et les étiquettes

        # Enregistrer chaque figure individuellement avec le nom de la forme
        plt.savefig(os.path.join(output_dir_plot, f"Sensitivity_on_share_and_shape_stacked_{shape}.png"), dpi=500)
        plt.close(fig)

    return None


def plot_stacked_revenues_by_shape_vertical_ok2(STORAGE_RESULT, params, output_dir_plot):
    # Obtenir toutes les formes uniques
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in STORAGE_RESULT.keys()))
    colors = ['#1f77b4', '#ff7f0e']  # Couleurs pour Market Revenue et Tariff Revenue
    bar_width = 0.4

    for shape in shapes:
        # Initialiser les listes pour chaque forme
        shares = []
        average_market_revenues = []
        average_tariff_revenues = []

        # Créer une nouvelle figure pour chaque forme
        fig, ax = plt.subplots(figsize=(6, 6))

        for scenario, df_delta in STORAGE_RESULT.items():
            if params[scenario]['global']['tariff']['shape'] == shape:
                # Calculer les revenus
                df_delta['revenue_net'] = df_delta['dispatch'] * df_delta['price']
                df_delta['revenue_tariff'] = df_delta['dispatch'] * df_delta['tariff']
                df_delta['revenue_market'] = df_delta['dispatch'] * df_delta['base_price']

                # Calculer les revenus annuels moyens
                annual_market_revenue = df_delta.groupby('year')['revenue_market'].sum().tolist()
                annual_tariff_revenue = df_delta.groupby('year')['revenue_tariff'].sum().tolist()

                # Calculer les revenus moyens
                average_market_revenue = np.mean(annual_market_revenue)
                average_tariff_revenue = np.mean(annual_tariff_revenue)

                # Lire le share
                share = float(params[scenario]['global']['tariff']['share'])

                # Stocker les valeurs
                shares.append(share)
                average_market_revenues.append(average_market_revenue)
                average_tariff_revenues.append(average_tariff_revenue)

        # Convertir les listes en arrays numpy
        shares = np.array(shares)
        average_market_revenues = np.array(average_market_revenues)
        average_tariff_revenues = np.array(average_tariff_revenues)

        # Tracer les bar charts pour la forme actuelle
        index = np.arange(len(shares))
        
        bars1 = ax.bar(index, average_market_revenues, bar_width, label='Energy market revenue', color=colors[0], edgecolor='black')
        bars2 = ax.bar(index, average_tariff_revenues, bar_width, bottom=average_market_revenues, label='Tariff-based revenue', color=colors[1], edgecolor='black')

        # Ajouter les annotations pour les pourcentages
        for bar1, bar2 in zip(bars1, bars2):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            total_height = height1 + height2

            if total_height > 0:
                market_pct = (height1 / total_height) * 100
                tariff_pct = (height2 / total_height) * 100

                # Ajuster les pourcentages pour qu'ils ne dépassent pas 100%
                #market_pct = min(market_pct, 100)
                #tariff_pct = min(tariff_pct, 100 - market_pct)

                ax.annotate(f'{market_pct:.1f}%', 
                            xy=(bar1.get_x() + bar1.get_width() / 2, height1 / 2), 
                            xytext=(0, 0), 
                            textcoords='offset points', 
                            ha='center', 
                            color='white',
                            fontsize=7)

                ax.annotate(f'{tariff_pct:.1f}%', 
                            xy=(bar2.get_x() + bar2.get_width() / 2, height1 + height2 / 2), 
                            xytext=(0, 0), 
                            textcoords='offset points', 
                            ha='center', 
                            color='black',
                            rotation='vertical',
                            fontsize=7)

        ax.set_xlabel('share')
        ax.set_ylabel('Average Revenue (EUR/y)')
        ax.set_title(f'{shape}')
        ax.set_xticks(index)
        ax.set_xticklabels([f'{share:.2f}' for share in shares])
        #ax.legend()

        # Créer une seule légende sous chaque figure
        ax.legend([bars1, bars2], labels=['Energy market revenue', 'Tariff-based revenue'], loc='lower center', ncol=2, bbox_to_anchor=(0.5, -0.15))

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.25)  # Ajuster la place pour la légende
        # Enregistrer chaque figure individuellement avec le nom de la forme
        plt.savefig(os.path.join(output_dir_plot, f"Sensitivity_on_share_and_shape_stacked_{shape}.png"), dpi=400)
        plt.close(fig)

    return None



def plotStorageDispatchConfiguration(scenario_cases, STORAGE_RESULT, params, output_dir_plot):
    # Obtenir toutes les formes et configurations uniques
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in scenario_cases))
    configs = sorted(set(params[scenario]['global']['tariff']['configuration'] for scenario in scenario_cases))
    
    # Déterminer la disposition des subplots
    n = len(shapes)
    m = len(configs)

    # Lire les paramètres globaux une seule fois
    year_plot = int(params[scenario_cases[0]]['global']['plot']['year_plot'])
    start_hour = int(params[scenario_cases[0]]['global']['plot']['start_hour'])
    end_hour = int(params[scenario_cases[0]]['global']['plot']['end_hour'])
    
    # Créer les subplots
    fig, axes = plt.subplots(n, m, figsize=(5 * m, 5 * n), sharey=True, sharex=True)

    if n == 1 and m == 1:
        axes = np.array([[axes]])  # S'assurer que axes soit toujours une matrice 2D
    elif n == 1:
        axes = np.array([axes])  # S'assurer que axes soit toujours une matrice 2D
    elif m == 1:
        axes = np.array([[ax] for ax in axes])  # S'assurer que axes soit toujours une matrice 2D

    for shape_idx, shape in enumerate(shapes):
        for config_idx, config in enumerate(configs):
            ax = axes[shape_idx, config_idx]

            
            for scenario in scenario_cases:
                if params[scenario]['global']['tariff']['shape'] == shape and params[scenario]['global']['tariff']['configuration'] == config:
                    # Sélectionner le dataframe correspondant
                    df = STORAGE_RESULT.get(scenario)

                    # Filtrer les données en fonction de year_plot, start_hour et end_hour
                    df_filtered = df[(df['year'] == year_plot) & 
                                        (df['hour'] >= start_hour) & 
                                        (df['hour'] <= end_hour)]

                    # Tracer les données
                    #df_filtered['dispatch']*= 10e3
                    ax.plot(df_filtered['hour'], df_filtered['dispatch_load'], label=f'Net load', color='b')
                    ax.plot(df_filtered['hour'], df_filtered['gridload'], label=f'Grid load ', color='g')
                    
                    if shape == "piecewise":
                        ax.plot(df_filtered['hour'], df_filtered['capacity limit'], label=f'Capacity Limit', color='r', linestyle='--')
                        ax.plot(df_filtered['hour'], df_filtered['capacity threshold'], label=f'Capacity Threshold ', color='m', linestyle='--')

            # Ajouter les titres et légendes
            ax.set_title(f'{shape} - {config}')
            if shape_idx == n - 1:  # Ajouter l'étiquette de l'axe des abscisses uniquement pour la dernière rangée
                ax.set_xlabel('Hour')
            if config_idx == 0:  # Ajouter l'étiquette de l'axe des ordonnées uniquement pour la première colonne
                ax.set_ylabel('Power(MW)')
            ax.legend()
            ax.grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "ex-ante_ex-post_dispatch_comparison.jpg"), dpi=600)

    return None



def plotStorageDispatchConfiguration_2(scenario_cases, STORAGE_RESULT, params, output_dir_plot):
    # Obtenir toutes les formes et configurations uniques
    shapes = sorted(set(params[scenario]['global']['tariff']['shape'] for scenario in scenario_cases))
    configs = sorted(set(params[scenario]['global']['tariff']['configuration'] for scenario in scenario_cases))
    
    # Déterminer la disposition des subplots
    n = len(shapes)
    m = len(configs)

    # Lire les paramètres globaux une seule fois
    year_plot = int(params[scenario_cases[0]]['global']['plot']['year_plot'])
    start_hour = int(params[scenario_cases[0]]['global']['plot']['start_hour'])
    end_hour = int(params[scenario_cases[0]]['global']['plot']['end_hour'])
    
    # Créer les subplots
    fig, axes = plt.subplots(n, m, figsize=(5 * m, 5 * n), sharey=True, sharex=True)

    if n == 1 and m == 1:
        axes = np.array([[axes]])  
    elif n == 1:
        axes = np.array([axes])  
    elif m == 1:
        axes = np.array([[ax] for ax in axes]) 

    for shape_idx, shape in enumerate(shapes):
        for config_idx, config in enumerate(configs):
            ax = axes[shape_idx, config_idx]

            
            for scenario in scenario_cases:
                if params[scenario]['global']['tariff']['shape'] == shape and params[scenario]['global']['tariff']['configuration'] == config:
                    # Sélectionner le dataframe correspondant
                    df = STORAGE_RESULT.get(scenario)

                    # Filtrer les données en fonction de year_plot, start_hour et end_hour
                    df_filtered = df[(df['year'] == year_plot) & 
                                        (df['hour'] >= start_hour) & 
                                        (df['hour'] <= end_hour)]

                    # Tracer les données
                    #df_filtered['dispatch']*= 10e3
                    ax.plot(df_filtered['hour'], df_filtered['total_demand'], label=f'Load during withdrawal', color='b') # injection_load
                    #ax.plot(df_filtered['hour'], df_filtered['gridload'], label=f'Grid load ', color='g')
                    ax.plot(df_filtered['hour'], df_filtered['gridload'], label='Grid load', color='g')
                    ax.plot(df_filtered['hour'], df_filtered['injection_load'], label=f'load during injection ', color='r')
                    
                    if shape == "piecewise":
                        ax.plot(df_filtered['hour'], df_filtered['capacity limit'], label=f'Capacity Limit', color='r', linestyle='--')
                        ax.plot(df_filtered['hour'], df_filtered['capacity threshold'], label=f'Capacity Threshold ', color='m', linestyle='--')

            # Ajouter les titres et légendes
            ax.set_title(f'{shape} - {config}')
            if shape_idx == n - 1:  # Ajouter l'étiquette de l'axe des abscisses uniquement pour la dernière rangée
                ax.set_xlabel('Hour')
            if config_idx == 0:  # Ajouter l'étiquette de l'axe des ordonnées uniquement pour la première colonne
                ax.set_ylabel('Power(MW)')
            ax.legend()
            ax.grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_plot, "ex-ante_ex-post_dispatch_separated_comparison.png"), dpi=400)

    return None

