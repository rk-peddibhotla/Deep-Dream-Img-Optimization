from IPython.display import Image, display
display(Image('images/14_deepdream_flowchart.png'))
display(Image('images/14_deepdream_recursive_flowchart.png'))


%matplotlib inline
import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
import random
import math
import PIL.Image
from scipy.ndimage.filters import gaussian_filter

print(tf.__version__)

import inception5h

inception5h.maybe_download()
model = inception5h.Inception5h()
print(len(model.layer_tensors))


def load_image(filename):
    image = PIL.Image.open(filename)
    return np.float32(image)

def save_image(image, filename):
    image = np.clip(image, 0.0, 255.0)
    image = image.astype(np.uint8)
    with open(filename, 'wb') as file:
        PIL.Image.fromarray(image).save(file, 'jpeg')


def plot_image(image):
    if False:
        image = np.clip(image/255.0, 0.0, 1.0).
        plt.imshow(image, interpolation=&#39;lanczos&#39;)
        plt.show()

    else:
        image = np.clip(image, 0.0, 255.0)
        image = image.astype(np.uint8)
        display(PIL.Image.fromarray(image))


def normalize_image(x):
    x_min = x.min()
    x_max = x.max()
    x_norm = (x - x_min) / (x_max - x_min)
    return x_norm


def plot_gradient(gradient):
    gradient_normalized = normalize_image(gradient)
    plt.imshow(gradient_normalized, interpolation='bilinear')
    plt.show()


def resize_image(image, size=None, factor=None):
    if factor is not None:
        size = np.array(image.shape[0:2]) * factor
        size = size.astype(int)
    else:
        size = size[0:2]
        size = tuple(reversed(size))

    img = np.clip(image, 0.0, 255.0)
    img = img.astype(np.uint8)
    img = PIL.Image.fromarray(img)
    img_resized = img.resize(size, PIL.Image.LANCZOS)
    img_resized = np.float32(img_resized)
    return img_resized


def get_tile_size(num_pixels, tile_size=400):
    num_tiles = int(round(num_pixels / tile_size))
    num_tiles = max(1, num_tiles)
    actual_tile_size = math.ceil(num_pixels / num_tiles)
    return actual_tile_size


def tiled_gradient(gradient, image, tile_size=400):
    grad = np.zeros_like(image)
    x_max, y_max, _ = image.shape
    x_tile_size = get_tile_size(num_pixels=x_max, tile_size=tile_size)
    x_tile_size4 = x_tile_size // 4
    y_tile_size = get_tile_size(num_pixels=y_max, tile_size=tile_size)
    y_tile_size4 = y_tile_size // 4
    x_start = random.randint(-3*x_tile_size4, -x_tile_size4)

    while x_start &lt; x_max:
        x_end = x_start + x_tile_size
        x_start_lim = max(x_start, 0)
        x_end_lim = min(x_end, x_max)
        y_start = random.randint(-3*y_tile_size4, -y_tile_size4)

        while y_start &lt; y_max:
            y_end = y_start + y_tile_size
            y_start_lim = max(y_start, 0)
            y_end_lim = min(y_end, y_max)
            img_tile = image[x_start_lim:x_end_lim, y_start_lim:y_end_lim, :]
            feed_dict = model.create_feed_dict(image=img_tile)
            g = session.run(gradient, feed_dict=feed_dict)
            g /= (np.std(g) + 1e-8)
            grad[x_start_lim:x_end_lim, y_start_lim:y_end_lim, :] = g
            y_start = y_end

        x_start = x_end
return grad


def optimize_image(layer_tensor, image, num_iterations=10, step_size=3.0,tile_size=400, show_gradient=False):
    img = image.copy()
    print("Image before:")
    plot_image(img)
    print("Processing image: ", end="")
    gradient = model.get_gradient(layer_tensor)
    for i in range(num_iterations):
        grad = tiled_gradient(gradient=gradient, image=img, tile_size=tile_size)
        sigma = (i * 4.0) / num_iterations + 0.5
        grad_smooth1 = gaussian_filter(grad, sigma=sigma)
        grad_smooth2 = gaussian_filter(grad, sigma=sigma*2)
        grad_smooth3 = gaussian_filter(grad, sigma=sigma*0.5)
        grad = (grad_smooth1 + grad_smooth2 + grad_smooth3)
        step_size_scaled = step_size / (np.std(grad) + 1e-8)
        img += grad * step_size_scaled
        if show_gradient:
            msg = "Gradient min: {0:&gt;9.6f}, max: {1:&gt;9.6f}, stepsize: {2:&gt;9.2f}";
            print(msg.format(grad.min(), grad.max(), step_size_scaled))
            plot_gradient(grad)
        else:
            print(&quot;. &quot;, end=&quot;&quot;)
    print()
    print(&quot;Image after:&quot;)
    plot_image(img)
    return img

def recursive_optimize(layer_tensor, image, num_repeats=4, rescale_factor=0.7, blend=0.2, num_iterations=10, step_size=3.0, tile_size=400):
    if num_repeats > 0:
        sigma = 0.5
        img_blur = gaussian_filter(image, sigma=(sigma, sigma, 0.0))
        img_downscaled = resize_image(image=img_blur, factor=rescale_factor)
        img_result = recursive_optimize(layer_tensor = layer_tensor, image = img_downscaled, num_repeats = num_repeats-1, rescale_factor=rescale_factor, blend=blend, num_iterations =num_iterations, step_size=step_size, tile_size= tile_size)
        img_upscaled = resize_image(image=img_result, size=image.shape)
        image = blend * image + (1.0 - blend) * img_upscaled
        print("Recursive level: ", num_repeats)
    else:
        img_result = optimize_image(layer_tensor=layer_tensor, image=image, num_iterations=num_iterations, step_size=step_size, tile_size=tile_size)
    return img_result

session = tf.InteractiveSession(graph=model.graph)

image = load_image(filename='images/hulk.jpg')
plot_image(image)
layer_tensor = model.layer_tensors[2]
img_result = optimize_image(layer_tensor, image, num_iterations=10, step_size = 6.0, tile_size= 400, show_gradient=True)
img_result = recursive_optimize(layer_tensor=layer_tensor, image=image, num_iterations=10, step_size=3.0, rescale_factor=0.7, num_repeats=4, blend=0.2)