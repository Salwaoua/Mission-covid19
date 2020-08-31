# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 15:16:24 2020

@author: souarraoui2
"""

import numpy as np
from numpy import exp
import matplotlib.pyplot as plt
#from scipy.integrate import odeinta
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import dash
import plotly.io as pio
import base64
import os 


#Data from Data Gouv : https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/


###############################################################################################
#--------------------------------DATA COLLECTION & MANAGEMENT---------------------------------#
###############################################################################################


#os.chdir("C:/Users/souarraoui2/Desktop/application_covid") 

# Data au departement/region


url_data_covid = 'https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c'
data_covid = pd.read_csv(url_data_covid, sep = ';')

data_population = pd.read_csv("fr_pop_region.csv", sep = ';')

correspondance_reg_dept = pd.read_csv("departements-region.csv", sep = ';',encoding='latin-1') 

# Data cas signalés france 
url_cas_france = 'https://www.coronavirus-statistiques.com/corostats/openstats/open_stats_coronavirus.csv'
data_cas_france = pd.read_csv(url_cas_france, sep = ';') 

#### Data a la region
# Extraction des cas signalés par region 
data_cas_region = data_cas_france.loc[data_cas_france.index.isin(['REG-84','REG-27','REG-53', 'REG-44', 'REG-32', 'REG-11','REG-28', 'REG-75', 'REG-76','REG-52','REG-93'])]

#### Data au national
data_cas_france = data_cas_france[data_cas_france['nom'] == 'france'] #filtre sur les données france uniquement
data_cas_france = data_cas_france[['date' , 'cas']]
data_cas_france = data_cas_france.rename(columns ={'date' : 'jour'})
data_cas_france['jour'] = pd.to_datetime(data_cas_france['jour'] , format="%Y/%m/%d")


# Correspondance entre fichier data au dpt et les regions
data_covid = data_covid.merge(correspondance_reg_dept, on='dep', how='left')

# Aggregation par region cas 
#data_covid_region = data_covid.groupby(['jour', 'region_name'])['incid_hosp', 'incid_dc', 'incid_rad','incid_rea'].apply(sum).reset_index()
data_covid_region = data_covid.groupby(['jour', 'region_name'])['incid_hosp', 'incid_dc', 'incid_rad','incid_rea'].agg('sum').reset_index()


# Ajout de la population générale
data_covid_region = data_covid_region.merge(data_population, on = 'region_name', how = 'left')





# Nlles colonnes cumul 

# 1 : format date 
data_covid_region['jour'] = pd.to_datetime(data_covid_region['jour'] , format="%Y/%m/%d")

# 2 : sort by date
data_covid_region = data_covid_region.sort_values(by = ['region_name', 'jour'])

# 3 : reset index
data_covid_region = data_covid_region.reset_index(drop = True) 

# 4: nouvelles colonnes Recovered, Hospitalisation total 
data_covid_region['deaths'] = data_covid_region.groupby('region_name')['incid_dc'].cumsum() 

data_covid_region['recovered'] = data_covid_region.groupby('region_name')['incid_rad'].cumsum() 

data_covid_region['hospitalises_daily'] = data_covid_region['incid_hosp'] + data_covid_region['incid_rea']
data_covid_region['hospitalises_cumul'] = data_covid_region.groupby('region_name')['incid_hosp'].cumsum() + data_covid_region.groupby('region_name')['incid_rea'].cumsum() 

data_covid_region['susceptibles'] = data_covid_region['population'] - data_covid_region['recovered'] - data_covid_region['hospitalises_cumul'] - data_covid_region['deaths']



## Nb de cas hospitalisés + rea & nb de cas signalés
cas_covid_total = data_covid_region.groupby('jour')['incid_hosp'].agg(['sum']) + data_covid_region.groupby('jour')['incid_rea'].agg(['sum'])
cas_covid_total = cas_covid_total.rename(columns ={'sum' : 'daily_cases_total'})
#cas_covid_total['jour'] = cas_covid_total.index
cas_covid_total = cas_covid_total.reset_index(drop=False) # index avec jours en col jours
cas_covid_total['cumul_cases_total'] =  cas_covid_total.daily_cases_total.cumsum() # calcul hosp/rea cumules
cas_covid_total = cas_covid_total.merge(data_cas_france, on = 'jour', how = 'inner') # ajout info cas cumules signales
cas_covid_total['cas'] = cas_covid_total['cas'].astype('Int64') # changement format colonne float to int
cas_covid_total['cas_jour'] = cas_covid_total['cas'].diff(1) # creation col cas journaliers
#cas_covid_total['cas_jour'] = [0 if i < 0 else i for i in cas_covid_total['cas_jour']] #remplace les valeurs négatives si pas de data au j+1
cas_covid_total = cas_covid_total.fillna(0)
cas_covid_total.cas_jour[cas_covid_total.cas_jour < 0] = 0




## Nb de dcd
cas_dc_total = data_covid_region.groupby('jour')['incid_dc'].agg(['sum']) # cumul des deces
cas_dc_total = cas_dc_total.rename(columns ={'sum' : 'daily_deaths_total'}) 
#cas_dc_total['jour'] = cas_dc_total.index
cas_dc_total['cumul_dc_total'] =  cas_dc_total.daily_deaths_total.cumsum() 

## Nb de recovered : rad
cas_recovered_total = data_covid_region.groupby('jour')['incid_rad'].agg(['sum']) 
cas_recovered_total = cas_recovered_total.rename(columns ={'sum' : 'daily_recovered_total'})
#cas_recovered_total['jour'] = cas_recovered_total.index
cas_recovered_total['cumul_recovered_total'] =  cas_recovered_total.daily_recovered_total.cumsum()



# Dataframes 
df_confirmed = data_covid_region[['jour', 'region_name','hospitalises_cumul', 'hospitalises_daily']]
df_deaths = data_covid_region[['jour', 'region_name','deaths', 'incid_dc']]
df_recovered = data_covid_region[['jour', 'region_name','recovered', 'incid_rad']]

 


# Data google mobilité 
#url_googlemobility = 'https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv?cachebust=20dfcade3402f1ab'
#data_google = pd.read_csv(url_googlemobility, sep = ',')

## Filtre sur la zone géographique étudiée 
#data_google = data_google[data_google['country_region'] == 'France']
#data_google = data_google.reset_index()

## Sélection des colonnes d'intérêt 
#data_google = data_google[['sub_region_1','date','retail_and_recreation_percent_change_from_baseline',
       #'grocery_and_pharmacy_percent_change_from_baseline',
       #'parks_percent_change_from_baseline',
       #'transit_stations_percent_change_from_baseline',
       #'workplaces_percent_change_from_baseline',
       #'residential_percent_change_from_baseline' ]]

## Data management du df 
#data_google['sub_region_1'] = data_google.sub_region_1.fillna('National')
#data_google['date'] = pd.to_datetime(data_google['date'] , format="%Y/%m/%d")
#data_google = data_google.fillna(0)

#data_google_region = data_google.groupby(['sub_region_1', 'date']).mean().round(1).reset_index()
#del(data_google)
#data_google_region = data_google_region.replace('Brittany', 'Bretagne')
#data_google_region = data_google_region.replace('Normandy', 'Normandie')
#data_google_region = data_google_region.replace('Corsica', 'Corse')

## fichier propre : apres data management 
data_google_region = pd.read_csv('donnees_google_region.csv')
data_google_region = data_google_region[['sub_region_1','date','retail_and_recreation_percent_change_from_baseline',
       'grocery_and_pharmacy_percent_change_from_baseline',
       'parks_percent_change_from_baseline',
       'transit_stations_percent_change_from_baseline',
       'workplaces_percent_change_from_baseline',
       'residential_percent_change_from_baseline' ]]
data_google_region['date'] = pd.to_datetime(data_google_region['date'] , format="%Y/%m/%d")



###############################################################################################
#-----------------------------------------------DASH------------------------------------------#
###############################################################################################



tickFont = {'size':20, 'color':"rgb(30,30,30)", \
            'family':"Courier New, monospace"}
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.config.suppress_callback_exceptions = True


# Récupération des images et fonds
image_filename = 'ilis.png' 
image_filename2 = 'ilis2.png'

encoded_image = base64.b64encode(open(image_filename, 'rb').read())  
encoded_image2 = base64.b64encode(open(image_filename2, 'rb').read())  


#app.title = 'Mission Covid-19'

# Styles

colors = {
    'background': '#0c2032',
    'text': '#617487',
    'figure_text': '#f1f1f1',
    'confirmed_text':'#3CA4FF',
    'deaths_text':'#f44336',
    'recovered_text':'#5A9E6F',
    'highest_case_bg':'#393939',
    
}

divBorderStyle = {
    'backgroundColor' : '#1b3147',
    'borderRadius': '12px',
    'lineHeight': 0.9,
}

boxBorderStyle = {
    'borderColor' : '#1b3147',
    'borderStyle': 'solid',
    'borderRadius': '10px',
    'borderWidth':2,
}


fig = go.Figure()

# Fonction pour plot national 
def draw_global_graph(cas_covid_total,cas_recovered_total,cas_dc_total,type_graph='daily'):

    if type_graph == 'daily':
    
         fig = go.Figure(go.Scatter(x=cas_covid_total['jour'], y=cas_covid_total['daily_cases_total'],
                                mode='lines+markers',
                                name='Hospitalisés',
                                line=dict(color='#cc1f53', width=2),
                                fill='tozeroy',))
    
         fig.add_trace(go.Scatter(x=cas_covid_total['jour'], y=cas_covid_total['cas_jour'],
                                mode='lines+markers',
                                name='Cas confirmés',
                                line=dict(color='#3372FF', width=2),
                                fill='tozeroy',))
         fig.add_trace(go.Scatter(x=cas_recovered_total.index, y=cas_recovered_total['daily_recovered_total'],
                                mode='lines+markers',
                                name='Remis',
                                line=dict(color='#33FF51', width=2),
                                fill='tozeroy',))
         fig.add_trace(go.Scatter(x=cas_dc_total.index, y=cas_dc_total['daily_deaths_total'],
                                mode='lines+markers',
                                name='Décès',
                                line=dict(color='#FF3333', width=2),
                                fill='tozeroy',))
         fig.add_shape(dict(
                type="line",
                x0='2020-05-11',
                y0=0,
                x1='2020-05-11',
                y1=max(cas_covid_total['cas_jour'])+1000,
                line=dict(
                    color="#ffffff",
                    width=3)))
         
         fig.add_annotation(x = '2020-05-11', y = max(cas_covid_total['cas_jour']),
                             text = 'Date de déconfinement')
         
         fig.add_shape(dict(
                type="line",
                x0='2020-07-20',
                y0=0,
                x1='2020-07-20',
                y1=max(cas_covid_total['cas_jour'])+1000,
                line=dict(
                    color="#ffffff",
                    width=3)))
         
         fig.add_annotation(x = '2020-07-20', y = max(cas_covid_total['cas_jour']),
                             text = 'Date port du masque obligatoire')
         

    else :
        
        
         fig = go.Figure(go.Scatter(x=cas_covid_total['jour'], y=cas_covid_total['cumul_cases_total'],
                                mode='lines+markers',
                                name='Hospitalisés',
                                line=dict(color='#cc1f53', width=2),
                                fill='tozeroy',))
         fig.add_trace(go.Scatter(x=cas_covid_total['jour'], y=cas_covid_total['cas'],
                                mode='lines+markers',
                                name='Cas confirmés',
                                line=dict(color='#3372FF', width=2),
                                fill='tozeroy',))
         fig.add_trace(go.Scatter(x=cas_recovered_total.index, y=cas_recovered_total['cumul_recovered_total'],
                                mode='lines+markers',
                                name='Recovered',
                                line=dict(color='#33FF51', width=2),
                                fill='tozeroy',))
         fig.add_trace(go.Scatter(x=cas_dc_total.index, y=cas_dc_total['cumul_dc_total'],
                                mode='lines+markers',
                                name='Deaths',
                                line=dict(color='#FF3333', width=2),
                                fill='tozeroy',))
             
         fig.add_shape(dict(
                type="line",
                x0='2020-05-11',
                y0=0,
                x1='2020-05-11',
                y1=max(cas_covid_total['cas'])+15000,
                line=dict(
                    color="#ffffff",
                    width=3)))
         
         fig.add_annotation(x = '2020-05-11', y = max(cas_covid_total['cas']),
                             text = 'Date de déconfinement')
         
         fig.add_shape(dict(
                type="line",
                x0='2020-07-20',
                y0=0,
                x1='2020-07-20',
                y1=max(cas_covid_total['cas'])+15000,
                line=dict(
                    color="#ffffff",
                    width=3)))
         
         fig.add_annotation(x = '2020-07-20', y = max(cas_covid_total['cas']),
                             text = 'Date port du masque obligatoire')
         
         
        
    fig.update_layout(
            hovermode='x',
            font=dict(
                family="Courier New, monospace",
                size=14,
                color=colors['figure_text'],
            ),
            legend=dict(
                x=0.02,
                y=1,
                traceorder="normal",
                font=dict(
                    family="sans-serif",
                    size=12,
                    color=colors['figure_text']
                ),
                bgcolor=colors['background'],
                borderwidth=5
            ),
            paper_bgcolor=colors['background'],
            plot_bgcolor=colors['background'],
            margin=dict(l=0, 
                        r=0, 
                        t=0, 
                        b=0
                        ),
            height=400,
    
        )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')
    
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='#3A3A3A')
                     
                
                        
    return fig





# Fonction pour plot régional 
    
def draw_regional_graph(df_deaths,df_recovered,df_confirmed,type_graph2='deces'):
        
        if type_graph2 == 'deces':
            fig = go.Figure(go.Bar(x=df_deaths.region_name, y=df_deaths['deaths']))
            fig.update_traces(marker_color='#FF3333', marker_line_color='#FF3333',marker_line_width=1.5, opacity=0.6)
                    
        elif type_graph2 == 'guerisons' : 
            fig = go.Figure(go.Bar(x=df_recovered.region_name, y=df_recovered['recovered']))
            fig.update_traces(marker_color='#33FF51', marker_line_color='#33FF51',marker_line_width=1.5, opacity=0.6)

        
        else :
            fig = go.Figure(go.Bar(x=df_confirmed.region_name, y=df_confirmed['hospitalises_cumul']))
            fig.update_traces(marker_color='#cc1f53', marker_line_color='#cc1f53',marker_line_width=1.5, opacity=0.6)

 
    
        fig.update_layout(
            hovermode='x',
            font=dict(
                family="Courier New, monospace",
                size=14,
                color=colors['figure_text'],
            ),
            legend=dict(
                x=0.02,
                y=1,
                traceorder="normal",
                font=dict(
                    family="sans-serif",
                    size=12,
                    color=colors['figure_text']
                ),
                bgcolor=colors['background'],
                borderwidth=5
            ),
            paper_bgcolor=colors['background'],
            plot_bgcolor=colors['background'],
            margin=dict(l=0, 
                        r=0, 
                        t=0, 
                        b=0
                        ),
            height=500,
    
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')
    
        fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='#3A3A3A')

        return fig





# Mise en page du dashboard

app.layout = html.Div(
    [
        dcc.Tabs(id="tabs-example",
                value='tab-1-example',
                children=[
                        # Page 1 : présentation du projet 
                        dcc.Tab(label = 'Présentation du projet',
                                style={'fontSize':'30px','fontFamily':'Helvetica','fontWeight':'bold','border': '4px solid #1b3147','padding':'2px','backgroundColor':'#1b3147','marginTop':'8px','marginRight':'4px'},selected_style={'marginTop':'8px','marginRight':'4px','fontSize':'30px','fontWeight':'bold','border': '4px solid #617487','backgroundColor': '#617487','padding':'2px','fontFamily':'Helvetica'},
                                value='tab-1-example',
                                children = [
                                            html.Div(children=[
                        html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
                                 className='three columns',
                                 style={
                                            'height': '10%',
                                            'width': '10%',
                                            'float': 'left',
                                            #'position': 'relative',
                                            'margin-top': 10}),
                        html.Img(src='data:image/png;base64,{}'.format(encoded_image2.decode()),
                                 className='three columns',
                                 style={
                                            'height': '10%',
                                            'width': '8%',
                                            'float': 'right',
                                            #'position': 'relative',
                                            'margin-top': 10}),
                        html.H1(children = "Mission Covid-19",
                                           style={
                                                'textAlign': 'center',
                                                'color': colors['text'],
                                                'backgroundColor': colors['background'],
                                                'fontSize': 150
                                            },
                                            className='twelve columns',
                                            ),
                        html.H1(children = "Dans le cadre de notre Master 2 portant la mention \"Data Science pour la santé\", nous avons mobilisé\
                                            le maximum de nos savoirs et savoir-faire dans différentes disciplines enseignées. Ce projet porte sur \
                                            l'épidémie du Covid-19. Nous avons utilisé pour ce travail différentes sources de données nous vous proposons\
                                            à travers ce dashboard une visualisation de la donnée permattant de suivre l'évolution de la pandémie sur \
                                            le territoire français. Chaque onglet de ce dashboard porte des indicateurs et un maillage\
                                            géographique variable. Bonne lecture.",
                                           style={
                                                'textAlign': 'center',
                                                'color': colors['text'],
                                                'backgroundColor': colors['background'],
                                                'fontSize': 50
                                            },
                                            className='twelve columns',
                                            ),
                       
                        ]),
                                
                            
                        ]
                        
                        ),
                
     # Page 2 : Données nationales                   
    dcc.Tab(label='Données nationales',
                        style={'fontSize':'30px','fontFamily':'Helvetica','fontWeight':'bold','border': '4px solid #1b3147','padding':'2px','backgroundColor':'#1b3147','marginTop':'8px','marginRight':'4px'},selected_style={'marginTop':'8px','marginRight':'4px','fontSize':'30px','fontWeight':'bold','border': '4px solid #617487','backgroundColor': '#617487','padding':'2px','fontFamily':'Helvetica'},
                        value='tab-2-example',
                        children =[
                            html.Div(id='titre2',children=[
    html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
             className='three columns',
             style={
                        'height': '10%',
                        'width': '10%',
                        'float': 'left',
                        #'position': 'relative',
                        'margin-top': 10}),
    html.Img(src='data:image/png;base64,{}'.format(encoded_image2.decode()),
             className='three columns',
             style={
                        'height': '10%',
                        'width': '10%',
                        'float': 'right',
                        #'position': 'relative',
                        'margin-top': 10}),
    
    html.H4(children="""
                    Les données nationales du Covid-19
            """,
                             style={
                                 'textAlign': 'center',
                                 'color': colors['text'],
                                 'backgroundColor': colors['background'],
                                 'fontSize': 50,
    
                             },
                             className='twelve columns'
                             ),

    
    ]),
            
            
            
    ## Chiffres clés au national
       html.Div([ 
            html.Div([
                html.H4(children='Total cas hospitalisés: ',
                       style={
                           'textAlign': 'center',
                           'color': '#cc1f53',
                       }
                       ), 
                html.P(f"{cas_covid_total.cumul_cases_total.iloc[-1]:,d}",
                       style={
                    'textAlign': 'center',
                    'color': '#cc1f53',
                    'fontSize': 30,
                }
                ),
                html.P('Augmentation ces dernières 24h : +' + f"{cas_covid_total.cumul_cases_total.iloc[-1] - cas_covid_total.cumul_cases_total.iloc[-2]:,d}"
                       + ' (' + str(round(((cas_covid_total.cumul_cases_total.iloc[-1] - cas_covid_total.cumul_cases_total.iloc[-2])/cas_covid_total.cumul_cases_total.iloc[-1])*100, 2)) + '%)',
                       style={
                    'textAlign': 'center',
                    'color': '#cc1f53',
                }
                ),
                
            ],
                style=divBorderStyle,
                className='three columns',
            ),
    
    
            html.Div([
                html.H4(children='Total cas confirmés: ',
                       style={
                           'textAlign': 'center',
                           'color': colors['confirmed_text'],
                       }
                       ), 
                html.P(f"{cas_covid_total.cas.iloc[-1]:,d}",
                       style={
                    'textAlign': 'center',
                    'color': colors['confirmed_text'],
                    'fontSize': 30,
                }
                ),
                html.P('Augmentation ces dernières 24h : +' + f"{cas_covid_total.cas.iloc[-1] - cas_covid_total.cas.iloc[-2]:,d}"
                       + ' (' + str(round(((cas_covid_total.cas.iloc[-1] - cas_covid_total.cas.iloc[-2])/cas_covid_total.cas.iloc[-1])*100, 2)) + '%)',
                       style={
                    'textAlign': 'center',
                    'color': colors['confirmed_text'],
                }
                ),
                
            ],
                style=divBorderStyle,
                className='three columns',
            ),
    
    
            
    
            html.Div([
                html.H4(children='Total des Décès: ',
                       style={
                           'textAlign': 'center',
                           'color': colors['deaths_text'],
                       }
                       ),
                html.P(f"{cas_dc_total.cumul_dc_total.iloc[-1]:,d}",
                       style={
                    'textAlign': 'center',
                    'color': colors['deaths_text'],
                    'fontSize': 30,
                }
                ),
                html.P('Taux de mortalité: ' + str(round(cas_dc_total.cumul_dc_total.iloc[-1]/cas_covid_total.cumul_cases_total.iloc[-1] * 100, 3)) + '%',
                       style={
                    'textAlign': 'center',
                    'color': colors['deaths_text'],
                }
                ),
            ],
                style=divBorderStyle,
                className='three columns'),
    
    
            html.Div([
                html.H4(children='Total des retours à domicile: ',
                       style={
                           'textAlign': 'center',
                           'color': colors['recovered_text'],
                       }
                       ),
                html.P(f"{cas_recovered_total.cumul_recovered_total.iloc[-1]:,d}",
                       style={
                    'textAlign': 'center',
                    'color': colors['recovered_text'],
                    'fontSize': 30,
                }
                ),
                html.P('Taux de guérison: ' + str(round(cas_recovered_total.cumul_recovered_total.iloc[-1]/cas_covid_total.cumul_cases_total.iloc[-1]* 100, 3)) + '%',
                       style={
                    'textAlign': 'center',
                    'color': colors['recovered_text'],
                }
                ),
                
                
            ],
                style=divBorderStyle,
                className='three columns'),
    
    
         html.Div([html.Span('.',
                             style={'color': colors['text'],
                             }),
                       
                         ],className='twelve columns'
                         ),

    
         ## Création choix graphique : cumulé ou journalier
          html.Div([
            html.Div([
                dcc.Tabs(id='type_graph', value='total',
                children=[
                    dcc.Tab(label='Total cumulé', value='total',style={'fontSize':'16px','fontFamily':'Helvetica','fontWeight':'bold','border': '2px solid #1b3147','padding':'1px','backgroundColor':'#1b3147','marginTop':'4px','marginRight':'2px'},selected_style={'marginTop':'4px','marginRight':'2px','fontSize':'16px','fontWeight':'bold','border': '2px solid #617487','backgroundColor': '#617487','padding':'1px','fontFamily':'Helvetica'}),
                    dcc.Tab(label='Détail journalier', value='daily',style={'fontSize':'16px','fontFamily':'Helvetica','fontWeight':'bold','border': '2px solid #1b3147','padding':'1px','backgroundColor': '#1b3147','marginTop':'4px','marginLeft':'2px'},selected_style={'marginTop':'4px','marginLeft':'2px','fontSize':'16px','fontWeight':'bold','border': '2px solid #617487','backgroundColor': '#617487','padding':'1px','fontFamily':'Helvetica'}),
                ],style={'height':'34px'})
    ],className='twelve columns'), 
    
    
        ## Graphique national 
     html.Div([
                    dcc.Graph(
                        id='global-graph',

                    )
                ], className='twelve columns'
                ),

    
                    ])
    ]),
    ]
            ),
    
    
    
    
    
    
        # Page 3 : données régionales
            dcc.Tab(label='Données régionales',
                    value='tab-4-example',
                    style={'fontSize':'30px','fontFamily':'Helvetica','fontWeight':'bold','border': '4px solid #1b3147','padding':'2px','backgroundColor':'#1b3147','marginTop':'8px','marginRight':'4px'},selected_style={'marginTop':'8px','marginRight':'4px','fontSize':'30px','fontWeight':'bold','border': '4px solid #617487','backgroundColor': '#617487','padding':'2px','fontFamily':'Helvetica'},
                    children=[
                                    html.Div(id='titre3',children=[
    html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
             className='three columns',
             style={
                        'height': '10%',
                        'width': '10%',
                        'float': 'left',
                        #'position': 'relative',
                        'margin-top': 10}),
    html.Img(src='data:image/png;base64,{}'.format(encoded_image2.decode()),
             className='three columns',
             style={
                        'height': '10%',
                        'width': '10%',
                        'float': 'right',
                        #'position': 'relative',
                        'margin-top': 10}),
    
    html.H4(children="""
                    Les données régionales du Covid-19
            """,
                             style={
                                 'textAlign': 'center',
                                 'color': colors['text'],
                                 'backgroundColor': colors['background'],
                                 'fontSize': 50,
    
                             },
                             className='twelve columns'
                             ),
    ]),
    
       
                
        html.Div(id='right_container', children=[
           ## Choix quels chiffres : morts, hospitalisés ou guéris      
         html.Div([
                dcc.Tabs(id='type_graph2', value='deces',
                children=[
                    dcc.Tab(label='Total des décès', value='deces',style={'fontSize':'16px','fontFamily':'Helvetica','fontWeight':'bold','border': '2px solid #1b3147','padding':'1px','backgroundColor':'#1b3147','marginTop':'4px','marginRight':'2px'},selected_style={'marginTop':'4px','marginRight':'2px','fontSize':'16px','fontWeight':'bold','border': '2px solid #617487','backgroundColor': '#617487','padding':'1px','fontFamily':'Helvetica'}),
                    dcc.Tab(label='Total des guérisons', value='guerisons',style={'fontSize':'16px','fontFamily':'Helvetica','fontWeight':'bold','border': '2px solid #1b3147','padding':'1px','backgroundColor': '#1b3147','marginTop':'4px','marginLeft':'2px'},selected_style={'marginTop':'4px','marginLeft':'2px','fontSize':'16px','fontWeight':'bold','border': '2px solid #617487','backgroundColor': '#617487','padding':'1px','fontFamily':'Helvetica'}),
                    dcc.Tab(label='Total des hospitalisations', value='hospitalises',style={'fontSize':'16px','fontFamily':'Helvetica','fontWeight':'bold','border': '2px solid #1b3147','padding':'1px','backgroundColor': '#1b3147','marginTop':'4px','marginLeft':'2px'},selected_style={'marginTop':'4px','marginLeft':'2px','fontSize':'16px','fontWeight':'bold','border': '2px solid #617487','backgroundColor': '#617487','padding':'1px','fontFamily':'Helvetica'}),
                ],style={'height':'34px'})],className='twelve columns'),
                        
                        
         html.Div([html.Span('.', style={'color': colors['background'],'fontSize':'30px'}),
                   ], className = 'twelve columns'),
                        
        


            ## Graphique régional
          html.Div([
                    dcc.Graph(
                        id='recovered',
                    )
                ], className='eleven columns'
                ),
                    
    ]),    
                    ]),
           
        
        
        dcc.Tab(label='Données Google',
                    value='tab-5-example',
                    style={'fontSize':'30px','fontFamily':'Helvetica','fontWeight':'bold','border': '4px solid #1b3147','padding':'2px','backgroundColor':'#1b3147','marginTop':'8px','marginRight':'4px'},selected_style={'marginTop':'8px','marginRight':'4px','fontSize':'30px','fontWeight':'bold','border': '4px solid #617487','backgroundColor': '#617487','padding':'2px','fontFamily':'Helvetica'},
                    children=[
                                    html.Div(id='titre4',children=[
    html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
             className='three columns',
             style={
                        'height': '10%',
                        'width': '10%',
                        'float': 'left',
                        #'position': 'relative',
                        'margin-top': 10}),
    html.Img(src='data:image/png;base64,{}'.format(encoded_image2.decode()),
             className='three columns',
             style={
                        'height': '10%',
                        'width': '10%',
                        'float': 'right',
                        #'position': 'relative',
                        'margin-top': 10}),
    
    html.H4(children="""
                    Les données Google Mobility 
            """,
                             style={
                                 'textAlign': 'center',
                                 'color': colors['text'],
                                 'backgroundColor': colors['background'],
                                 'fontSize': 50,
    
                             },
                             className='twelve columns'
                             ),
                        
    html.Div([
    dcc.Dropdown(
        id='region_dropdown', value = 'National',
        options=[{'label': i, 'value': i} for i in list(data_google_region.sub_region_1.unique())],
        style = {'fontSize':'16px','fontFamily':'Helvetica','fontWeight':'bold','border': '2px solid #1b3147','padding':'1px','backgroundColor':'#1b3147','marginTop':'4px','marginRight':'2px'},
        #clearable=True,
    ),
                         html.Div(
                id='cx1'
                ), 
    ],className='twelve columns'),
                        
    
 
    ]),
                    ]),            
        ]),

        html.Div(id='tabs-content-example')
    ],className="row",
            style={
                'textAlign': 'left',
                'color': colors['text'],
                'backgroundColor': colors['background'],
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
            },
)
    
    
    
    
    
    


@app.callback(
    Output('global-graph', 'figure'),
    [Input('type_graph', 'value')])

def update_graph(type_graph):
    fig_global = draw_global_graph(cas_covid_total,cas_recovered_total,cas_dc_total,type_graph)
    return fig_global




@app.callback(
    Output('recovered', 'figure'),
    [Input('type_graph2', 'value')])
        
def update_graph_region(type_graph2):
    fig_region = draw_regional_graph(df_deaths,df_recovered,df_confirmed,type_graph2)
    return fig_region


@app.callback(Output('cx1', 'children'),
    [Input('region_dropdown', 'value')])
        

def update_figure(value):
    if value is None:
        dff = data_google_region
    else:
        dff = data_google_region.loc[data_google_region["sub_region_1"] == value]
    return html.Div(
            dcc.Graph(
                id='graph_3',
                figure={
                    "data": [
                        {"x": dff["date"],"y": dff["retail_and_recreation_percent_change_from_baseline"],
                         "name":"Commerces et loisirs","type": "lines+markers","marker": {"color": "#cc1f53"}},
                        {"x": dff["date"],"y": dff["grocery_and_pharmacy_percent_change_from_baseline"],
                         "name" :'Alimentation et pharmacies',
                         "type": "lines+markers","marker": {"color": "#3372FF"}},
                        {"x": dff["date"],"y": dff["parks_percent_change_from_baseline"],
                         "name":"Parcs","type": "lines+markers","marker": {"color": "#33FF51"}},
                        {"x": dff["date"],"y": dff["transit_stations_percent_change_from_baseline"],
                         "name":"Transports en commun","type": "lines+markers","marker": {"color": "#FF3333"}},
                        {"x": dff["date"],"y": dff["workplaces_percent_change_from_baseline"],
                         "name":"Lieux de travail","type": "lines+markers","marker": {"color": "#71EDFC"}},
                        {"x": dff["date"],"y": dff["residential_percent_change_from_baseline"],
                         "name":'Lieux et résidences',"type": "lines+markers","marker": {"color": "#A066B9"}},
                    ],
                    "layout": {
                        'title': 'Suivi journalier des déplacements des français par région',
                        "yaxis": {"title": "Evolution (en % )"},
                        'plot_bgcolor': colors['background'],
                        'paper_bgcolor': colors['background'],
                    },
                                   
                },
            )
    )



if __name__ == '__main__':
    app.run_server(debug=True)
    