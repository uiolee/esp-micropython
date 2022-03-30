# mpy.py
import os

# a script run on pc to `mpy-cross` all `.py` to `.mpy` file.

ls = [i for i in os.listdir() if i[-3:] == '.py']
[print(i) for i in ls]
print('\nconut: ', len(ls))

out = []
for i in ls:
    out.append(os.popen('mpy-cross {}'.format(i)).read())

print('--------------')
[print(i) for i in out if i]
print('--------------')

ls1 = [i for i in os.listdir() if i[-4:] == '.mpy']
[print(i) for i in ls1]
print('\nconut: ', len(ls1))

input('press any key to exit...')
