
import matplotlib.pyplot as plt
import numpy as np
from skimage import data

matplotlib.rcParams['font.size'] = 18

images = ('hubble_deep_field',
          'immunohistochemistry',
          'microaneurysms',
          'moon',
          'retina',
          'shepp_logan_phantom',
          'cell',
          )

camera = data.camera()

plt.figure(figsize=(4,4))
plt.imshow(camera, cmap='gray')
plt.axis('off')
plt.show()

camera[:10] = 0

plt.figure(figsize=(4,4))
plt.imshow(camera, cmap='gray')
plt.axis('off')
plt.show()

mask = camera < 87

plt.figure(figsize=(4,4))
plt.imshow(camera, cmap='gray')
plt.axis('off')
plt.show()

camera[mask] = 255

plt.figure(figsize=(4,4))
plt.imshow(camera, cmap='gray')
plt.axis('off')
plt.show()

inds_x = np.arange(len(camera))
inds_y = (4*inds_x) % len(camera)
camera[inds_x, inds_y] = 0

plt.figure(figsize=(4,4))
plt.imshow(camera, cmap='gray')
plt.axis('off')
plt.show()

l_x, l_y = camera.shape[0], camera.shape[1]
X, Y = np.ogrid[:l_x, :l_y]
outer_disk_mask = (X - l_x /2)**2 + (Y - l_y / 2)**2 > (l_x / 2)**2
camera[outer_disk_mask] = 0

plt.figure(figsize=(4,4))
plt.imshow(camera, cmap='gray')
plt.axis('off')
plt.show()

#for name in images:
#    caller = getattr(data, name)
#    image = caller()
#    plt.figure()
#    plt.title(name)
#    if image.ndim == 2:
#        plt.imshow(image, cmap=plt.cm.gray)
#    else:
#        plt.imshow(image)
#
#plt.show()