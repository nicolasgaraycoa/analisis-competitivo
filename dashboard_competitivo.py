import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import statistics
import seaborn as sns
from datetime import datetime, timedelta


st.set_page_config(page_title="Dashboard analisis competitivo", layout="wide")

st.subheader('Analisis competitivo')

precios = pd.read_excel('precios.xlsx')
precios['quarter'] = pd.PeriodIndex(precios['fecha'], freq='Q').to_timestamp().date
conversiones = pd.read_excel('precios.xlsx',2)
precios = precios.merge(conversiones, left_on = 'pais', right_on='pais', how='left')
precios['precio'] = precios['precio']*precios['conversion']
precios.drop(['moneda', 'conversion'], axis=1, inplace=True)



with st.sidebar:
    fecha_min, fecha_max = st.select_slider(
    'Rango de trimestres',
    options=list(precios['quarter']),
    value=(min(precios['quarter']), max(precios['quarter'])))

    pais = st.multiselect(
             'Pais:',
            list(precios.pais.unique()),
            default=['francia'])
    
    competidores = st.selectbox(
             '\# Competidores:',
            (1,2,3,4,5))
    

precios['precio'] = (statistics.mode(precios['ml'])/precios['ml'])*precios['precio']
precios = precios[precios['pais'].str.contains('|'.join(map(str, pais)))]

me = pd.read_excel('precios.xlsx',1)
me.dropna(inplace=True)

me = precios[['marca', 'sku', 'precio']].merge(me, left_on=['marca', 'sku'], right_on=['marca', 'sku'], how='left')
me.dropna(inplace=True)
me['m']=me['precio']/me['e']

d4 = precios[precios['empresa']=='oliver']
d4 = d4[['pais', 'sku', 'precio']].groupby(by=['pais', 'sku'], as_index=False).agg('mean')
d4['precio'] = round(d4['precio'],2)

fig4 = px.scatter(d4, y='sku', x='precio', color='pais', height=660, opacity=0.6, title="Precio x SKU x pais")
fig4.update_traces(marker=dict(size=19))
fig4.update_layout(yaxis={'categoryorder':'total ascending'})
fig4.update_layout(yaxis_title=None)



fig5 = px.scatter(me[['sku', 'e', 'm']].groupby(by='sku', as_index=False).agg('mean').round(2),
                   y='m', x='e', color='sku', height=500, opacity=0.6, title="E x M")
fig5.update_traces(marker=dict(size=19))
fig5.add_hline(y=3.5, line_dash="dash", opacity=0.3)



def comparables(dx, n):
    da = dx[dx['empresa']=='oliver']
    da = da[['sku', 'precio']].groupby(by='sku', as_index=False).agg('mean')
    db = dx[['sku', 'precio']].groupby(by='sku', as_index=False).agg('mean')
    db = db[~db['sku'].isin(da['sku'])]

    solution = pd.DataFrame()
    counter = 0
    for i in da['precio']:
        dist = []
        for j in db['precio']:
            dist.append(abs(j - i))
        comp_index = sorted(range(len(dist)), key=lambda i: dist[i])[:n]
        df_temp = pd.concat([db.iloc[comp_index].reset_index(drop=True),
                                 pd.Series([da['sku'].iloc[counter]] * n, name='sku_ref')], axis=1)
        solution = pd.concat([solution, df_temp], axis=0)
        counter += 1
    
    da['sku_ref'] = da['sku']
    solution = pd.concat([solution,da], axis=0).reset_index(drop=True)
    solution['precio'] = round(solution['precio'],2)

    return solution



tab1, tab2 = st.tabs(["Marcas", "Retailers"])

with tab1:
    col7, col8, col9, col10 = st.columns(4)
    with col7:
        st.metric("Presidente", '{}x'.format(round(np.mean(me['m'][me['marca']=='presidente']),2)), delta=0, delta_color="normal")

    with col8:
        st.metric("Opthimus", '{}x'.format(round(np.mean(me['m'][me['marca']=='opthimus']),2)), delta=0, delta_color="normal")

    with col9:
        st.metric("Quorhum", '{}x'.format(round(np.mean(me['m'][me['marca']=='quorhum']),2)), delta=0, delta_color="normal")
    
    with col10:
        st.metric("Unhiq", '{}x'.format(round(np.mean(me['m'][me['marca']=='unhiq']),2)), delta=0, delta_color="normal")
    
    col11, col12 = st.columns(2)
    with col11:
        st.plotly_chart(fig4, theme="streamlit", use_container_width=True)
    with col12:
        fig_comp = px.scatter(comparables(precios, competidores),
                               y='sku_ref', x='precio', color='sku', height=660, opacity=0.6, title="Precio x SKU vs closest comparable(s)")
        fig_comp.update_traces(marker=dict(size=19))
        fig_comp.update_layout(yaxis={'categoryorder':'total ascending'})
        fig_comp.update_layout(yaxis_title=None)
        st.plotly_chart(fig_comp, theme="streamlit", use_container_width=True)
    st.plotly_chart(fig5, theme="streamlit", use_container_width=True)
    

        

share = precios[['tienda', 'empresa', 'sku']]
share['oliver_bin'] = np.where(share['empresa']=='oliver',1,0)
share = share.groupby(by=['tienda', 'empresa'], as_index=False).agg({'oliver_bin': 'sum', 'sku':'count'})
share = share[['tienda', 'oliver_bin', 'sku']].groupby(by=['tienda'], as_index=False).sum()
share['percent'] = round((share['oliver_bin']/share['sku']),6)
share = round(share['percent'].mean(),6)


d1 = precios[['pais', 'sku', 'precio']].groupby(by=['pais','sku'], as_index=False).agg('mean')
d1.columns = ['pais', 'sku', 'precio_promedio']
d1 = precios[['pais', 'sku', 'tienda','precio']].merge(d1, left_on=['pais', 'sku'], right_on=['pais','sku'], how='left')
d1['porcentaje_var'] = ((d1['precio']/d1['precio_promedio'])-1)*100
d1 = d1[['pais', 'tienda', 'porcentaje_var']].groupby(by=['pais', 'tienda'], as_index=False).agg('mean')
d1['porcentaje_var'] = round(d1['porcentaje_var'],1)
rango_pvp = (max(d1['porcentaje_var'])-min(d1['porcentaje_var']))/100

d2 = precios[['pais','sku','precio']].groupby(by=['pais','sku'], as_index=False).agg('mean')
d2['ptier'] = pd.qcut(d2['precio'].rank(method='first'), q=5, labels=['core','premium', 'super premium', 'ultra premium', 'luxury'])
d2 = d2[['pais','sku', 'ptier']]
d2.drop_duplicates(inplace =True)
d2 = precios[['pais','tienda', 'empresa','sku', 'precio']].drop_duplicates().merge(d2, left_on=['pais','sku'], right_on=['pais','sku'], how='left')
d2 = d2.merge(d2[['pais', 'tienda', 'ptier','precio']].groupby(by=['pais', 'tienda', 'ptier'], as_index=False).agg('mean'), 
                 left_on=['pais', 'tienda', 'ptier'], right_on=['pais', 'tienda', 'ptier'], how='left')
d2.columns = ['pais', 'tienda', 'empresa', 'sku', 'precio', 'ptier', 'ptier_mean']
d2 = d2[d2['empresa']=='oliver']
d2['percent'] = (d2['precio']/d2['ptier_mean'])-1
d2 = d2[['tienda', 'ptier', 'percent']].groupby(by=['tienda', 'ptier'], as_index=False).agg('mean')
posicionamiento = np.mean(d2['percent'])
rango_pos = max(d2['percent'].dropna())-min(d2['percent'].dropna())
d2['percent'] = round(d2['percent'],4)*100

with tab2:
    col1, col2, col3, col4 = st.columns(4)
    with col1: 
        st.metric("Share of shelf ", "{:.0%}".format(share), delta=0, delta_color="normal")
    with col2:
        st.metric("Rango de variacion de PVP ", "{:.0%}".format(rango_pvp), delta=0, delta_color="normal")
    with col3: 
        st.metric("Posicionamiento precio/segmento ", "{:.0%}".format(posicionamiento), delta=0, delta_color="normal")
    with col4:
       st.metric("Rango de variacion de posicionamiento", "{:.0%}".format(rango_pos), delta=0, delta_color="normal") 
   
    col5, col6 = st.columns(2)
    with col5:      
       fig1 = px.bar(d1, y='tienda', x='porcentaje_var', height = 690, color='pais', barmode='group', title="Variacion del PVP promedio x retailer x pais")
       fig1.update_layout(yaxis={'categoryorder':'total ascending'})
       fig1.update_layout(xaxis_title="(%) variacion")
       fig1.update_layout(yaxis_title=None)

       st.plotly_chart(fig1, theme="streamlit", use_container_width=True)
    
    with col6:
       fig2 = px.scatter(d2, y='tienda', x='percent', color='ptier', height=690, opacity=0.6, title="Posicionamiento x retailer x segmento de precio")
       fig2.update_traces(marker=dict(size=19))
       fig2.add_vline(x=0, line_dash="dash", opacity=0.3)
       fig2.update_layout(yaxis={'categoryorder':'total ascending'})
       fig2.update_layout(xaxis_title="(%) variacion")
       fig2.update_layout(yaxis_title=None)

       st.plotly_chart(fig2, theme="streamlit", use_container_width=True)

    
   
    d3 = precios[['tienda', 'marca', 'sku']]
    d3 = d3.groupby(by=['tienda', 'marca'], as_index=False).agg({'sku':'count'})
    d3 = d3.merge(precios[['tienda', 'sku']].groupby(by='tienda', as_index=False).agg('count'), left_on='tienda', right_on='tienda', how='left')
    d3.columns= ['tienda', 'marca', 'count', 'total']
    d3['percent'] = round(d3['count']/d3['total'],2)*100
    d3 = d3[['tienda', 'marca', 'percent']]
    d3 = d3.pivot(index='tienda',columns='marca',values='percent')
    d3.fillna(0, inplace=True)
    d3.loc['promedio'] = d3.mean()

    cm = sns.light_palette("green", as_cmap=True)

    st.markdown('**Share of shelf x retailer x marca**')
    st.dataframe(d3.style.format('{:.0f}%',precision=0).background_gradient(cmap=cm, axis=1), use_container_width=True)
