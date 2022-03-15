# Тестовое задание для проекта Kotlin/Native: musl-based target

Выполнил: Степан Остапенко.

## Python-скрипты

### Скрипт для компиляции clang

В файле `compile-clang.py` расположен скрипт для компиляции clang из исходников с github.

Скрипт работает следующим образом: если в папке со скриптом нету исходников, скрипт загружает их с помощью `git clone`; далее в папке `llvm-project/build-v1` с использованием стандартного компилятора для C/C++ собирается первая версия clang; дальнейшие версии собираются в папках `llvm-project/build-v2`, `llvm-project/build-v3`, ..., каждая следующая версия компилируется с использованием предыдущей. В процессе сборки скрипт записывает номер последней собранной версии в файл `.clang-from-sources-latest-available-version`.

В переменной `ACTUAL_GIT_BRANCH` в скрипте указано имя ветки с версией LLVM, которая будет использована для работы.

Использование:
```
usage: compile-clang.py [-h] [-j THREADS] [-n STEPS | -a ADD]

Script to compile clang from sources.

optional arguments:
  -h, --help            show this help message and exit
  -j THREADS, --threads THREADS
                        number of threads to work with (default: 1)
  -n STEPS, --steps STEPS
                        initial bootstrap steps count (default: 1)
  -a ADD, --add ADD     additional bootstrap steps count
```

Параметр `THREADS` отвечает за количество потоков, которые будут использоваться для сборки.

Параметр `STEPS` отвечает за то, сколько "поколений" компилятора будет собрано (в процессе работы появятся папки `build-v1`, `build-v2`, ..., `build-v<STEPS>`). При использовании этого параметра перед запуском произойдет отчистка всех собранных ранее файлов. Например, вызов
```console
~/src/musl-test-task$ ./compile-clang.py --steps 3
```
создаст первую, вторую и третью версию ("поколение") clang, предварительно удалив все собранные ранее файлы.

Параметр `ADD` отвечает за добавление определённого количества версий ("поколений") компилятора. При использовании этого параметра скрипт определит последнюю собранную версию clang (прочитав информацию из файла `.clang-from-sources-latest-available-version`) и добавит еще `ADD` новых версий ("поколений") после неё. Например, вызов
```console
~/src/musl-test-task$ ./compile-clang.py --add 2
```
при наличии трёх уже собранных "поколений" компилятора добавит четвертое и пятое "поколение" clang, не удаляя уже существующие файлы сборки.

Параметры `STEPS` и `ADD` нельзя использовать вместе.

### Скрипт-обёртка для компилятора

В файле `wrapper.py` расположен скрипт-обёртка для компилятора. В качестве параметров командной строки нужно передать опции, которые должны быть переданы компилятору (скрипт просто вызывает компилятор с параметрами, переданными ему). Если скрипт находит рядом с собой папку `llvm-project`, в которой есть информация об уже собранных версиях компилятора, он вызывает последнюю из них. Если скрипт не находит чего-либо из этого, он запускает `compile-clang.py` и собирает первую версию clang.

Я не нашёл адекватного способа сборки программы, которая будет печатать время своей компиляции при каждом запуске, поэтому для создания таких программ мне пришлось немного модифицировать переданные аргументы и имена исполняемых файлов. По-факту всё происходит так: если результат компиляции нужно записать в файл `<out>`, то результат компиляции запишется в файл `<out>-binary-file-<хэш строки <out>>`, и вместе с ним будет создан Python-скрипт с именем `<out>`, который будет печатать время компиляции в стандартный поток ошибок и запускать сам скомпилированный файл. При запуске скомпилированного файла скрипт передаёт все свои аргументы командной строки в качестве аргументов к запускаемому файлу, а также привязывает все свои стандартные потоки ввода/вывода/ошибок к стандартным потокам запускаемого файла.

Пример скрипта, полученного при компиляции исполняемого файла `sample`:
```python
#!/usr/bin/python3

# This is an automatically generated wrapper script for executable "sample".
# It executes file "sample-binary-file-5e8ff9bf55ba3508199d22e984129be6".

import sys
import subprocess

print("This executable was compiled at 2022-03-14 15:01:38.723186.", file = sys.stderr)

args = sys.argv
args[0] += "-binary-file-5e8ff9bf55ba3508199d22e984129be6"
subprocess.Popen(args = args, stdin = sys.stdin, stdout = sys.stdout, stderr = sys.stderr)
```
Таким образом, результат компиляции будет записан в файл с названием `sample-binary-file-5e8ff9bf55ba3508199d22e984129be6`. При запуске этого скрипта командой `./sample <args> < <inf> > <ouf>` будет напечатано время компиляции, а после этого будет запущен новый процесс с командой `./sample-binary-file-5e8ff9bf55ba3508199d22e984129be6 <args>` и привязанными стандартными потоками ввода/вывода/ошибок.

Стоит отметить, что из-за такого способа реализации скрипт можно использовать только для компиляции исполняемых файлов, но не объектных файлов или библиотек.

## Результаты

### Clang компилятор

С помощью скрипта я скомпилировал 10 "поколений" clang и записал время, затраченное на компиляцию:
```
Version  1 was built in 6793.68757961805 s
Version  2 was built in 6006.74157810112 s
Version  3 was built in 5545.15148830438 s
Version  4 was built in 5605.12498068805 s
Version  5 was built in 5594.95433473587 s
Version  6 was built in 5523.26750183105 s
Version  7 was built in 5524.67198997755 s
Version  8 was built in 5526.48536083987 s
Version  9 was built in 5536.27846125229 s
Version 10 was built in 5528.23906083221 s
```

Нетрудно заметить, что сначала с каждым новым "поколением" время компиляции уменьшается, а, начиная с шестого "поколения", стабилизируется. Это связано с тем, что clang кодирует команды оптимальнее, чем g++, используемый при исходной компиляции, поэтому с каждым новым проходом набор команд оптимизируется, что приводит к немного улучшенному результату на следующем шаге, и т. д.

### Wrapper

Пример компиляции и запуска программы `hw.cpp` с помощью скрипта `wrapper.py`:
```c++
#include <iostream>

using namespace std;

int main(int argc, char **argv) {
  cout << "Hello, World!" << endl;
  
  for (int i = 0; i < argc; i++) {
    cout << argv[i] << " ";
  }
  cout << endl;

  string s;
  while (cin >> s) {
    cerr << "cerr: " << s << endl;
    cout << s << endl;
  }

  return 0;
}
```
```console
~/Desktop$ ~/src/musl-test-task/wrapper.py hw.cpp -o hw
Compiling executable "hw" using clang version from build-v10.

~/Desktop$ cat hw
#!/usr/bin/python3

# This is an automatically generated wrapper script for executable "hw".
# It executes file "hw-binary-file-65c2a3d77127c15d068dec7e00e50649".

import sys
import subprocess

print("This executable was compiled at 2022-03-14 15:01:52.439888.", file = sys.stderr)

args = sys.argv
args[0] += "-binary-file-65c2a3d77127c15d068dec7e00e50649"
subprocess.Popen(args = args, stdin = sys.stdin, stdout = sys.stdout, stderr = sys.stderr)

~/Desktop$ cat inf
sample input file
1
2
3
4 5 6
@@@@@@@@

~/Desktop$ ./hw few sample args 1 2 3 < inf > ouf
This executable was compiled at 2022-03-14 15:01:52.439888.
cerr: sample
cerr: input
cerr: file
cerr: 1
cerr: 2
cerr: 3
cerr: 4
cerr: 5
cerr: 6
cerr: @@@@@@@@

~/Desktop$ cat ouf
Hello, World!
./hw-binary-file-65c2a3d77127c15d068dec7e00e50649 few sample args 1 2 3 
sample
input
file
1
2
3
4
5
6
@@@@@@@@
```
