# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 04:22:05 2023

@author: Nelson.Chung
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 03:59:37 2022

In this program, I scrape NCAA women's soccer game-level data and create a computer poll based on 
margin-of-victory.

@author: Owner
"""
#Include only teams that have played a minimum of 6 games
min_games=6

from selenium import webdriver as wd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
from pandas.io.html import read_html
import time

import numpy as np
import re
import pandas as pd
import os 
import itertools as it
import xlrd as xl
from datetime import datetime, date, timedelta
os.chdir('c:/Sabr')

#Add the winner and loser columns with the same school
def combo(colnum):
    print(colnum)
    #Check if any of the loser columns matches the winner column
    global l
    if l.isin([w[colnum]]).any():
        #find out which column
        spot=l.index[l.eq(w[colnum])]
        #If there's a match, add that loser column to the winner column
        finw.iloc[:,colnum]+=finl.iloc[:,spot[0]]

#Create an empty data frame to stack games on
games=pd.DataFrame()

start_dt=date(2023,8,17)
end_dt=date.today()

dates=[]
delta=timedelta(1)

while start_dt<=end_dt:
    dates.append(start_dt)
    start_dt+=delta

dt_fmt=[datetime.strftime(i,'%Y/%m/%d') for i in dates]

#Open each page
for k in dt_fmt:
    driver=wd.Chrome()
    driver.get('https://www.ncaa.com/scoreboard/soccer-women/d1/'+str(k)+'/all-conf')
    time.sleep(5)
    pg=driver.find_element_by_xpath('//*[(@id = "scoreboardGames")]')
    page_txt=pg.get_attribute('innerHTML')
    num_games=len(re.findall('game-'+'\d',page_txt))
   
    #Extract each game
    for m in range(num_games):
        box=driver.find_element_by_xpath('//*[(@id = "game-'+str(m)+'")]')
        game=box.get_attribute('innerHTML')
        name='<span class="gamePod-game-team-name">(.*?)</span>'
        score='<span class="gamePod-game-team-score">(.*?)</span>'
        status='<div class="gamePod-status">(.*?)</div>'
        vis=re.findall(name,game)[0]
        hom=re.findall(name,game)[1]
        if re.findall(score,game)[0]=='':
            vis_score=''
        else:
            vis_score=int(re.findall(score,game)[0])
        if re.findall(score,game)[1]=='':
            hom_score='' 
        else:
            hom_score=int(re.findall(score,game)[1])
        status=re.findall(status,game)[0]
        cols=['vis','vis_score','hom','hom_score','status']
        obs=pd.DataFrame([[vis,vis_score,hom,hom_score,status]],columns=cols)
        obs['Date']=k
        games=pd.concat([games,obs],axis=0)
    if obs.empty:
        print('No Games on '+str(k))
    else:
        print(k)

    driver.close()
    

#Include only finished games
fin=games[games.status=='FINAL'].reset_index()
#Identify winners, losers, 
fin['winner']=np.where(pd.to_numeric(fin.hom_score)>pd.to_numeric(fin.vis_score),fin.hom,fin.vis)
fin['loser']=np.where(pd.to_numeric(fin.hom_score)>=pd.to_numeric(fin.vis_score),fin.vis,fin.hom)
fin['loser']=np.where(fin.winner==fin.loser,np.where(fin.winner==fin.hom,fin.vis,fin.hom),fin.loser)   
fin['mov']=abs(pd.to_numeric(fin.hom_score)-pd.to_numeric(fin.vis_score))
fin['hg']=np.where(fin.mov==0,0,np.where(fin.hom==fin.winner,1,-1))
            

#Create Dummy Variables for victors and losers
finw=pd.get_dummies(fin[['winner']]) 
finl=(-1)*pd.get_dummies(fin[['loser']])

#Delete winner_ and loser_ from the front of column titles, create series from the columns
finw.columns=finw.columns.str.lstrip('winner_')
finl.columns=finl.columns.str.lstrip('loser_')
w=pd.Series(finw.columns)
l=pd.Series(finl.columns)

finwo=finw.copy()


#Transfer the -1's from the loss matrix to the win matrix    
for v in (range(len(finw.columns))):
    combo(v)

#Get the colum names from the loss matrix that aren't in the win matrix, add those columns to the win matrix to create the wl matrix
cols=finl.columns.difference(finw.columns)
wl=pd.concat([finw,finl[cols]],axis=1)

#Combine the WL matrix with the non-dummies
findumb=pd.concat([fin,wl],axis=1)





#Check if the number of teams is correct  
vh=pd.concat([fin.vis,fin.hom]).unique()
if len(vh)==len(wl.columns):
    print('Felicidades! You have the correct number of teams! You are ready to run a regression.')
else:
    print('Your number of teams are off.')
    



#Export

# y=fin[(fin.vis=='BYU')|(fin.hom=='BYU')]

# yfd=findumb[(findumb.BYU==1)|(findumb.BYU==-1)]

# yfin=findumb[['BYU','mov']]


#C R E A T E    W I N - L O S S   R E C O R D S

#Subtract tie games from wins and losses totals
wmov=pd.concat([findumb.mov,finwo],axis=1) #Add MOV to the original winner matrix

#Mark ties
for r in wmov.columns[1:]:
    wmov[r]=np.where(wmov.mov==0,0,wmov[r])
    
lmov=pd.concat([findumb.mov,finl],axis=1) #Add MOV to the loser matrix
for s in lmov.columns[1:]:
    lmov[s]=np.where(lmov.mov==0,0,lmov[s])
 
    
#Sum all wins from from dummy matrix     
wins=pd.DataFrame(wmov.agg('sum'))
wins['team']=wins.index
wins['wins']=wins[0]

losses=pd.DataFrame(lmov.agg('sum'))
losses['team']=losses.index
losses['losses']=abs(losses[0])

wins_losses=pd.merge(wins,losses,how='outer',on='team')

findumb['tie']=np.where(findumb.mov==0,1,0)
w_tie=findumb[findumb.tie==1][['winner','tie']]
l_tie=findumb[findumb.tie==1][['loser','tie']].rename(columns={'loser':'winner'})
ties=pd.concat([w_tie,l_tie],axis=0)
ties['ties']=ties.groupby(['winner'])['tie'].transform('sum')
tie_agg=ties.drop_duplicates()

wins_losses_ties=pd.merge(wins_losses,tie_agg,how='outer',left_on='team',right_on='winner')[['team','wins','losses','ties']].fillna(0)
wins_losses_ties['games']=wins_losses_ties.wins+wins_losses_ties.losses+wins_losses_ties.ties
#Teams that have played at least 
d1=wins_losses_ties[wins_losses_ties.games>min_games]

findumb=findumb[(findumb.hom.isin(d1.team) & findumb.vis.isin(d1.team))].drop(columns='tie')

#Export matrix to Excel for Regression
findumb.to_excel('games_soccer.xlsx',index=False)


#Export WL record to Excel
wins_losses_ties.to_excel('soccer_WLT.xlsx',index=False)

# byu=findumb[findumb.BYU!=0]

# byu=wmov[wmov.BYU!=0]

# byu=finwo[finwo.BYU!=0]


# byu=finw[finw.BYU!=0]

# byu=fin[(fin.hom=='BYU')|(fin.vis=='BYU')]


byu=games[(games.hom=='BYU')|(games.vis=='BYU')]
# import pandas as pd
# import os
# os.chdir('c:/Sabr/')
games=pd.read_excel('games_soccer.xlsx')
fsu=games[(games.vis=='Florida St.')|(games.hom=='Florida St.')]
byu=games[(games.hom=='BYU')|(games.vis=='BYU')]
# unf=games[(games.vis=='North Florida')|(games.hom=='North Florida')]

sd=games[(games.vis=='San Diego')|(games.hom=='San Diego')]
ucla=games[(games.vis=='UCLA')|(games.hom=='UCLA')]
tex=games[(games.vis=='Texas')|(games.hom=='Texas')]



