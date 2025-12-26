# Rapport de projet — Dashboard d'analyse Olist

Réalisé par : Mouad Hida

Date : 2025-12-26

## 1. Contexte
Ce projet fournit un tableau de bord interactif pour analyser le dataset "Brazilian E-Commerce" (Olist). L'application permet d'explorer les commandes, les produits, les vendeurs, les paiements, les avis clients et des informations de géolocalisation via des visualisations modernes (Plotly + Streamlit).

## 2. Objectifs
- Fournir des indicateurs clés (KPIs) : nombre de commandes, chiffre d'affaires, clients uniques, performance de livraison.
- Visualiser les séries temporelles (commandes / revenus).
- Identifier les produits et vendeurs les plus performants.
- Analyser la distribution des avis clients.
- Explorer la performance de livraison (delta estimé vs réalisé).
- Visualiser des points géographiques (si présents) sur une carte.

## 3. Données utilisées
Les fichiers CSV attendus (dans le dossier `data/`) :
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_geolocation_dataset.csv`

Ces jeux de données proviennent du dataset public `olistbr/brazilian-ecommerce`.

## 4. Principales fonctionnalités implémentées
- Chargement robuste des CSV avec fallback d'encodage.
- Fusion des tables pour créer un `master` dataset utilisé par les graphiques.
- Génération d'alias lisibles pour `product_id` (`P0001`, ...) et `seller_id` (`S0001`, ...) pour améliorer l'affichage.
- KPIs affichés en haut du dashboard.
- Graphiques interactifs Plotly : courbes, barres, scatter, area, carte Mapbox (OpenStreetMap).
- Gestion optionnelle de la régression linéaire (trendline) via `statsmodels` (si installé).

## 5. Limitations et améliorations futures
- La carte utilise des colonnes détectées automatiquement; la qualité dépend des colonnes présentes.
- Les alias d'ID sont générés selon l'ordre d'apparition — on peut les regénérer selon d'autres règles (par chiffre d'affaires, fréquence, etc.).
- Ajouter analyses avancées : cohorte, funnel, churn, heatmaps par état/ville.

## 6. Fichiers clés
- `dashboard.py` — application Streamlit principale.
- `requirements.txt` — dépendances Python.
- `download_kaggle.py` — script optionnel pour télécharger les données depuis Kaggle.
- `save_to_sqlite.py` — script pour sauvegarder `orders` dans une base SQLite locale.

## 7. Auteur
Mouad Hida
