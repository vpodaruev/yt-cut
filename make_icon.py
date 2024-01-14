#!/usr/bin/env python3

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
import numpy as np

plt.style.use('_mpl-gallery')


def get_components(color, linewidth):
    circle = Circle((0, 0), radius=1.0, color=color,
                    fill=False, linewidth=linewidth)

    t = np.array([a / 180. * np.pi for a in (150, 270, 30)])
    x = 0.90 * np.cos(t)
    y = 0.90 * np.sin(t)
    triangle = Polygon(np.array([x, y]).T, color=color,
                       fill=False, linewidth=linewidth)

    dot = Circle((0, 0), radius=0.1 * linewidth / 12.0, color=color)

    return (circle, triangle, dot)


# plot
fig, ax = plt.subplots(figsize=(5, 5))

# background layer (white)
for item in get_components("w", 32.0):
    ax.add_patch(item)

# foreground layer (black)
for item in get_components("k", 12.0):
    ax.add_patch(item)

ax.set(xlim=(-1.1, 1.1), xticks=[],
       ylim=(-1.1, 1.1), yticks=[])
ax.set_frame_on(False)

plt.savefig("icons/ytcut.png", transparent=True)
plt.show()
