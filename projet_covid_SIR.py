# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 15:16:24 2020

@author: souarraoui2
"""

import numpy as np
from numpy import exp
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import pandas as pd
import plotly.graph_objects as go



###############################################################################################
#--------------------------------DATA COLLECTION & MANAGEMENT---------------------------------#
###############################################################################################


url_cas_france = 'https://www.coronavirus-statistiques.com/corostats/openstats/open_stats_coronavirus.csv'
data_cas_france = pd.read_csv(url_cas_france, sep = ';') 

# Population France
data_population = pd.read_excel("C:/Users/souarraoui2/Desktop/data_projet_covid/fr_population.region.departement.xls", 
                                head = True)

# 2 # DATA MANAGEMENT

# Extraction data france et format du dataframe

def data_manag(data):
   
    data = data[data['nom'] == 'france'] 
    
    data = data[['date', 'cas', 'deces', 'guerisons']] # garde les col d'intérêt
    
    data['date'] = data.index # col date a partir de l'index
    data['date'] = pd.to_datetime(data_cas_france['date'] , format="%Y/%m/%d")

    data = data.reset_index(drop = True) # reinitialisation de l'index
    data = data.fillna(0)
    
    return(data)
    
data_covid = data_manag(data_cas_france)  

# Population totale france
pop_tot = data_population.population.sum()

# Ajout nouvelles colonnes 

data_covid['recovered_cumul'] = data_covid['guerisons'] + data_covid['deces'] # Colonne correspondante aux recovered
data_covid['cas_journaliers'] = data_covid['cas'].diff(1) # creation col cas journaliers
data_covid['susceptibles'] = pop_tot - data_covid['recovered_cumul'] - data_covid['cas']




# 3 # Variables  

# Temps de guérison 
temps_guerison = 7

# Taux reproduction moyen 
taux_reproduction = 3.5

# Split data par périodes : 

## Sans confinement : on garde un r0 à 3.5 pendant tout la période  
data_covid_sansconfinement = data_covid[(data_covid['date'] >= '2020-02-21') & (data_covid['date'] < '2020-06-30')]
data_covid_sansconfinement = data_covid_sansconfinement.reset_index(drop = True)

# Nb de jours sur période
ndays_sansconfinement = data_covid_sansconfinement['date'].nunique()

# Cas initiaux 
initial_cas = data_covid_sansconfinement.cas.iloc[0]
initial_gueris = data_covid_sansconfinement.recovered_cumul.iloc[0] 
days = ndays_sansconfinement


###############################################################################################
#-------------------------------------DATA VISUALISATION--------------------------------------#
###############################################################################################

#### Fonction de lissage
def lissage(Lx,Ly,p):
    Lxout=[]
    Lyout=[]
    for i in range(p,len(Lx)-p):
        Lxout.append(Lx[i])
    for i in range(p,len(Ly)-p):
        val=0
        for k in range(2*p):
            val+=Ly[i-p+k]
        Lyout.append(val/2/p)
            
    return Lxout,Lyout

I_x, I_y = lissage(data_covid_sansconfinement.index, data_covid_sansconfinement['cas_journaliers'], 15)
R_x, R_y = lissage(data_covid_sansconfinement.index, data_covid_sansconfinement['recovered_cumul'], 15)
S_x, S_y = lissage(data_covid_sansconfinement.index, data_covid_sansconfinement['susceptibles'], 15)





#### Graphique data covid réelles 

def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)

fig, host = plt.subplots(figsize=(10,6))

fig.suptitle('Nombre total de cas covid19 en France au cours du temps', fontsize=25)
fig.subplots_adjust(right=0.75)

par1 = host.twinx()
par2 = host.twinx()

# Offset the right spine of par2.  The ticks and label have already been
# placed on the right by twinx above.
par2.spines["right"].set_position(("axes", 1.2))
# Having been created by twinx, par2 has its frame off, so the line of its
# detached spine is invisible.  First, activate the frame but make the patch
# and spines invisible.
make_patch_spines_invisible(par2)
# Second, show the right spine.
par2.spines["right"].set_visible(True)

p1, = host.plot(S_x, S_y, "b-", label="Susceptibles")
p2, = par1.plot(R_x, R_y, "g-", label="Recovered")
p3, = par2.plot(I_x, I_y, "r-", label="Infected")



host.set_ylabel("Susceptibles")
par1.set_ylabel("Recovered")
par2.set_ylabel("Infected")
host.set_xlabel('Jour')


host.yaxis.label.set_color(p1.get_color())
par1.yaxis.label.set_color(p2.get_color())
par2.yaxis.label.set_color(p3.get_color())

tkw = dict(size=4, width=1.5)
host.tick_params(axis='y', colors=p1.get_color(), **tkw)
par1.tick_params(axis='y', colors=p2.get_color(), **tkw)
par2.tick_params(axis='y', colors=p3.get_color(), **tkw)
host.tick_params(axis='x', **tkw)

fig, par1 = plt.ylim(0, 15000)
fig, par1 = plt.axvline(x=25,color='k', linestyle='--')


 
lines = [p1, p2, p3]
host.legend(lines, [l.get_label() for l in lines])







###############################################################################################
#-------------------------------------------SIR MODEL-----------------------------------------#
###############################################################################################

#https://github.com/XuelongSun/Dynamic-Model-of-Infectious-Diseases/blob/master/SIR.ipynb


# population totale
N = pop_tot
# nb cas initiaux et gueris initiaux 
I0,R0 = initial_cas, initial_gueris
# taux de reproduction 
r0 = taux_reproduction
# population susceptible d'être malade
S0 = N - I0 - R0
# taux de transmission de la maladie (beta) et temps moyen de guérison (gamma = 1/jours de guérison)
gamma = 1/temps_guerison
beta = gamma*r0
    
def fonction_derivation(y,t,N,beta,gamma):
    S,I,R = y 
    dSdt = -beta*S*I/N
    dIdt = beta*S*I/N - gamma*I
    dRdt = gamma*I
    return dSdt, dIdt, dRdt
    
# Grille temporelle
t = np.linspace(0,days,days)
    
# Vecteur SIR initial
y = S0,I0,R0
# Equations SIR dans la grille temps 
ret = odeint(fonction_derivation, y, t, args = (N,beta,gamma))
S,I,R = ret.T
    
fig, ax = plt.subplots(figsize=(10,6))
fig.suptitle('Modélisation SIR: nombre de cas au cours du temps', fontsize=25)
ax.plot(S, c='b', lw=2, label='S')
ax.plot(I, c='r', lw=2, label='I')
ax.plot(R, c='g', lw=2, label='R')
ax.set_xlabel('Jour',fontsize=20)
ax.set_ylabel('Nombre de cas', fontsize=20)
ax.grid(1)
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)
plt.legend();
    
    
    




