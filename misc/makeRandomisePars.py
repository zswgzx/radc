import numpy as np

# define # subjects
len=254

# make design matrix
a=np.loadtxt('age-tp1').reshape((len,1))
b=a-np.average(a)
a=np.ones((len,1))
b=np.concatenate((a,b),axis=1)

np.savetxt('age-tp1-demeaned',b,fmt='%.5f')

# make contrast
a=np.linspace(1,0,2,dtype='uint8').reshape((1,2))

np.savetxt('contrast',a,fmt='%2i')
