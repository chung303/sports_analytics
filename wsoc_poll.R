#In this program, I import an Excel spreadsheet of NCAA women soccer games and
# create a computer poll using a regression on margin-of-victory. Then I import 
# another spreadsheet of win-loss totals for all schools, to merge with with the 
# rankings.

library(readxl)
library(insight)
setwd('c:/Sabr/soccer')
wsoc<-subset(read_excel('c:/Sabr/games_soccer.xlsx'),select = -c(1:9))
#Run and examing the regression
summary(lm(mov~.,data=wsoc))
ncaa_reg<-data.frame(coef(summary(lm(mov~.,data=wsoc)))) #Extract coefficients
ncaa_reg<-ncaa_reg[order(ncaa_reg$Estimate,decreasing = T),] #Rank teams by their coefficients (=rating)
ncaa_reg$rank<-1:nrow(ncaa_reg) #Give each team a ranking
ncaa_reg$team<-row.names(ncaa_reg)
ncaa_reg$team<-text_remove_backticks(ncaa_reg$team)

wlt<-read_excel('c:/Sabr/soccer_WLT.xlsx') #Import spreadsheet with win-loss records Merge the regression coefficients with won-loss records

ncaa_reg_wlt<-merge(ncaa_reg,wlt,by='team',all.x=T,sort=F) #Merge the regression coefficients with won-loss records
ncaa_rank<-ncaa_reg_wlt[order(ncaa_reg_wlt$Estimate,decreasing=T),]
ncaa_rank$record<-paste(ncaa_rank$wins,'',ncaa_rank$losses,'',ncaa_rank$ties)

#Export results to CSV
write.csv(ncaa_rank,file='ncaa_soccer_reg.csv')

