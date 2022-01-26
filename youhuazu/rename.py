import os
import pandas as pd
df=pd.read_csv(r'city.txt')
files=os.listdir(r'all_files')
s=0
s2=0
for file in files:
    s2+=1
    # print(file)
    for i in range(len(df)):
        lon=file.split('_')[2]
        lat=file.split('_')[3]
        # print(((float(lat)-float(df.iloc[:,2][i]))**2+(float(lon)-float(df.iloc[:,3][i]))**2))
        if ((float(lat)-float(df.iloc[:,2][i]))**2+(float(lon)-float(df.iloc[:,3][i]))**2)<0.:
            oldname=file
            newname=file.split('.csv')[0]+df.iloc[:,1][i]+'.csv'
            # print(file,df.iloc[:,2][i],df.iloc[:,3][i],i,df.iloc[:,1][i])
            # print(newname)
            s+=1
            os.rename('all_files/{}'.format(oldname),'all_files/{}'.format(newname))
            print(s,s2)
        # else:print('wu')
    # print('over',file)

