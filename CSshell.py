import main
import os
import platform

print('+------------------------------------------------------+')
print('|             Welcome to CS - v1.0.0 alpha             |')
print('|              Developed By Coretan Senja              |')
print('+------------------------------------------------------+')
print("| Operating System : " + platform.system() +
      "                         []|")
print("| Release          : " + platform.release() +
      "                              []|")
print("| PS Version       : v1.0 alpha                      []|")
print('+------------------------------------------------------+\n')


while True:

    text = input('Coretan_senja ~> ')
    result, error = main.run('<stdin>', text)

    if error:
        print(error.as_string())
    elif result:
        print(repr(result))
