import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)

# load data
rot = np.loadtxt('rot-absDiff')
trans = np.loadtxt('trans-absDiff')

# set thresholds
rot_threshold = .02
rot_thresholds = [None] * len(rot)
for i in range(len(rot)):
    rot_thresholds[i] = rot_threshold

trans_threshold = 1.
trans_thresholds = [None] * len(trans)
for i in range(len(trans)):
    trans_thresholds[i] = trans_threshold

# plot figures
fig, ax = plt.subplots()
ax.plot(np.arange(1,len(rot)+1), rot_thresholds, 'r--', range(1,len(rot)+1), rot, 'b*')
plt.xlabel('subject')
plt.ylabel('avg. rotation diff. (rad)')
plt.title('Difference of average rotation (about z axis) between odd/even slices across subjects')
plt.axis(xmin=0, xmax=len(rot)+1., ymin=0, ymax=np.max(rot))
plt.grid(which='both', axis='x', linestyle='--')

# https://matplotlib.org/gallery/ticks_and_spines/major_minor_demo.html
majorLocator = MultipleLocator(50)
majorFormatter = FormatStrFormatter('%d')
minorLocator = MultipleLocator(10)

ax.xaxis.set_major_locator(majorLocator)
ax.xaxis.set_major_formatter(majorFormatter)

# for the minor ticks, use no labels; default NullFormatter
ax.xaxis.set_minor_locator(minorLocator)

mng = plt.get_current_fig_manager()
mng.full_screen_toggle()
plt.subplots_adjust(.039, .058, .99, .965)
plt.show()
fig.savefig('rot-z.png')

# -----
fig, ax = plt.subplots()
ax.plot(np.arange(1,len(trans)+1), trans_thresholds, 'r--', range(1,len(trans)+1), trans[:,0], 'b*')
plt.xlabel('subject')
plt.ylabel('avg. translation diff. (mm)')
plt.title('Difference of average translation (about x axis) between odd/even slices across subjects')
plt.axis(xmin=0, xmax=len(trans)+1., ymin=0, ymax=np.max(trans[:,0]))
plt.grid(which='both', axis='x', linestyle='--')

majorLocator = MultipleLocator(50)
majorFormatter = FormatStrFormatter('%d')
minorLocator = MultipleLocator(10)

ax.xaxis.set_major_locator(majorLocator)
ax.xaxis.set_major_formatter(majorFormatter)
ax.xaxis.set_minor_locator(minorLocator)

mng = plt.get_current_fig_manager()
mng.full_screen_toggle()
plt.subplots_adjust(.032, .058, .99, .965)
plt.show()
fig.savefig('trans-x.png')

# -----
fig, ax = plt.subplots()
ax.plot(np.arange(1,len(trans)+1), trans_thresholds, 'r--', range(1,len(trans)+1), trans[:,1], 'b*')
plt.xlabel('subject')
plt.ylabel('avg. translation diff. (mm)')
plt.title('Difference of average translation (about y axis) between odd/even slices across subjects')
plt.axis(xmin=0, xmax=len(trans)+1., ymin=0, ymax=np.max(trans[:,1]))
plt.grid(which='both', axis='x', linestyle='--')

majorLocator = MultipleLocator(50)
majorFormatter = FormatStrFormatter('%d')
minorLocator = MultipleLocator(10)

ax.xaxis.set_major_locator(majorLocator)
ax.xaxis.set_major_formatter(majorFormatter)
ax.xaxis.set_minor_locator(minorLocator)

mng = plt.get_current_fig_manager()
mng.full_screen_toggle()
plt.subplots_adjust(.032, .058, .99, .965)
plt.show()
fig.savefig('trans-y.png')
plt.close(fig='all')
