# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39

import shutil
from distutils import spawn
import tempfile
import os
import subprocess

def system(argv, *, catch=None, **kwargs):
  r = subprocess.run(argv, capture_output=True, text=True, **kwargs)
  if r.returncode:
    if catch is not None:
      # catch(r) returns the alternate stdout for handled errors
      o = catch(r)
      # if catch(r) returns None, the error is unexpected and should be raised
      if o is not None: return o
    raise Exception(f'Fail to run {argv} (code={r.returncode}): {r.stderr}')
  return r.stdout

def write_extra_input(x, file):
  if type(x) == str:
    print(x, file=file)
  else:
    for line in x:
      print(line, file=file)

def compile(
  input_path, addr=None,
  extra_c_flags=[],
  extra_as_input=[], extra_as_flags=[],
  extra_ld_input=[], extra_ld_flags=[],
):
  distDir = tempfile.mkdtemp()
  distASM, distOBJ, distLD, distLOBJ, distBIN = (f'{distDir}/_.{ext}' for ext in ['s', 'o', 'ld', 'l.o', 'bin'])

  try:
    input_name = input_path.rsplit('.', 1)[0]

    if input_path.endswith('.c'):
      # compile to OBJ
      system([
        'powerpc-eabi-gcc',
        '-fno-asynchronous-unwind-tables',
        ','.join((
          '-Wa', '-mregnames', '-mgekko',
          *extra_as_flags,
        )),
        '-c', '-o', distOBJ,
        *extra_c_flags,
        input_path,
      ])
    else: # treat as ASM file
      # make ASM file
      with open(distASM, 'w') as fw, open(input_path, 'r') as fr:
        write_extra_input(extra_as_input, file=fw)
        for line in fr: fw.write(line)
      # assemble to OBJ
      system([
        'powerpc-eabi-as',
        '-mregnames', '-mgekko',
        '-o', distOBJ,
        *extra_as_flags,
        distASM,
      ])

    # link
    with open(distLD, 'w') as fw:
      inputLD = input_name+'.ld'
      ## extra ld
      if os.path.isfile(inputLD):
        with open(inputLD) as f:
          fw.write(f.read())
      ## section
      print('SECTIONS {', file=fw)
      if addr is not None: print(f'  . = {addr};', file=fw)
      print('  .text : ALIGN(4) { *(.text) }', file=fw)
      if addr is not None: print('.rodata : ALIGN(4) { *(.rodata) }', file=fw)
      print('}', file=fw)
      write_extra_input(extra_ld_input, file=fw)
    system([
      'powerpc-eabi-ld',
      '-o', distLOBJ,
      '-T', distLD,
      *extra_ld_flags,
      distOBJ,
    ])

    # gecko symbols
    symbols = {}
    errmsg_nosymbol = "section '.text' mentioned in a -j option, but not found in any input file"
    lines = system([
      'powerpc-eabi-objdump',
      '-tj.text', distLOBJ,
    ], catch=lambda r: '' if r.returncode==1 and errmsg_nosymbol in r.stderr else None).split('\n')
    for line in lines[4:-3]:
      ch1, ch2 = line.split('\t')
      addr = int(ch1.split(None, 2)[0], 16)
      name = ch2.split()[1]
      symbols[name] = addr

    # binary
    system([
      'powerpc-eabi-objcopy',
      '-O', 'binary',
      distLOBJ, distBIN,
    ])
    with open(distBIN, 'rb') as f:
      codeBin = f.read()

    return codeBin, symbols

  finally:
    shutil.rmtree(distDir)
