#!/usr/bin/env python3

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
import numpy as np

plt.style.use('_mpl-gallery')

# plot
fig, ax = plt.subplots(figsize=(5, 5))

circle = Circle((0, 0), radius=1.0, color="k", fill=False, linewidth=12.0)
ax.add_patch(circle)

t = np.array([a / 180. * np.pi for a in (150, 270, 30)])
x = 0.95 * np.cos(t)
y = 0.95 * np.sin(t)
triangle = Polygon(np.array([x, y]).T, color="k", fill=False, linewidth=12.0)
ax.add_patch(triangle)

circle = Circle((0, 0), radius=0.1, color="k")
ax.add_patch(circle)

ax.set(xlim=(-1.05, 1.05), xticks=[],
       ylim=(-1.05, 1.05), yticks=[])
ax.set_frame_on(False)

plt.savefig("icons/ytcut.png", transparent=True)
plt.show()
