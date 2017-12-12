import random

from PIL import Image

for x in xrange(20000):
    print(x)
    r = lambda: random.choice(range(1, 228))
    img = Image.new('RGB', (r(), r()), (r(), r(), r()))
    img.save('./gen_images/img' + str(x) + ".jpg", "JPEG")
