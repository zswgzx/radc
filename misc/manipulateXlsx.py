import pandas as pd
from os import system

# read excel file
df = pd.read_excel('~/work/misc/melissa/pr803/r14/qsm/R14_QSM.xlsx')
# df = pd.read_csv('R2.csv')

# show first/last 5 rows
df.head()
df.tail()

# change format of date to YYMMDD
df['mri_date']=df['mri_date'].dt.strftime('%y%m%d')
# df['mri_date']=pd.to_datetime(df['mri_date']).dt.strftime('%y%m%d')

# show fu_year and projid with zero pad format
df['fu_year']=df['fu_year'].apply(lambda x: '%02d' % x)
df['projid']=df['projid'].apply(lambda x: '%08d' % x)

# select rows with specific column label
df = df.loc[df['scan_num'] == '1']

# sort by specific column label
df = df.sort_values(by=['mri_date', 'fu_year', 'projid'], ascending=True)

# drop columns that are unnecessary
df=df.drop(columns=['study','diff_first2second','age_abl'])

# reorder columns
df=df[df.columns[[2,1,0,3,4,5,6]]]

# save to csv format
df.to_csv('test1.csv', header=None, index= False)

# run system command
system("cat test1.csv |tr ',' '_' > subjs;rm test1.csv")


