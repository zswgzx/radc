import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)

# load data
df = pd.read_csv('./csvs/data.csv', header=None)

dim = df.shape
for index in list(range(dim[0])):
    iqm = df.iloc[index][0]
    vals = df.iloc[index][1:]

    # plot figures
    fig, ax = plt.subplots()
    ax.plot(range(1,len(vals)+1), vals, 'b*')
    plt.xlabel('subjects')
    plt.ylabel(iqm)
    plt.title('IQM for {}'.format(iqm))
    plt.axis(xmin=0, xmax=len(vals)+1, ymin=np.min(vals), ymax=np.max(vals))
    plt.grid(which='both', axis='x', linestyle='--')

    minorLocator = MultipleLocator(10)
    ax.xaxis.set_minor_locator(minorLocator)

    mng = plt.get_current_fig_manager()
    mng.full_screen_toggle()
    #plt.subplots_adjust(.032, .058, .99, .965)
    plt.show()
    fig.savefig('{}.png'.format(iqm))

    plt.close(fig='all')
