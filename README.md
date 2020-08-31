# Mission-covid19 

Dans le cadre de notre Master 2 portant la mention "Data Science pour la santé", nous avons mobilisé le maximum de nos savoirs et savoir-faire dans différentes disciplines enseignées. Ce projet porte sur l'épidémie du Covid-19. Nous avons utilisé pour ce travail différentes sources de données nous vous proposons à travers ce dashboard une visualisation de la donnée permettant de suivre l'évolution de la pandémie sur le territoire français. Chaque onglet de ce dashboard porte des indicateurs et un maillage géographique variable. Bonne lecture.

## Le code est découpé en plusieurs étapes :

- Les INPUTS : avec data collection et data management
  - Une partie data collection automatique:
    - les données data gouv
    - les données statistiques coronavirus 
  - Une partie pour le chargement des fichiers csv nécessaires : 
    - une table de correspondance régions-départements français
    - une table avec la population française recensée par région en 2020
    - les données Google Mobility préalablement nettoyées et transformée
  - Une partie de data management des données 
  
- Les OUTPUTS : Le DASH
   - Avec les fonctions permettant la création des graphiques 
   - Le code de mise en oeuvre de l'application Dash
   - La partie callbacks 


Dashboard disponible sur : http://app-covid19-salwaoua.herokuapp.com/
