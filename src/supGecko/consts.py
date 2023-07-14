# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39

CMP_IDX = {'==': 0, '!=': 2, '>': 4, '<': 6}
UNIT_IDX = {
   8: 0, 'b': 0, 'byte': 0,
  16: 1, 'h': 1, 'halfword': 1,
  32: 2, 'w': 2, 'word': 2,
}
REGOP_IDX = {
  'add': 0, '+': 0,
  'mul': 1, '*': 1,
  'or' : 2, '|': 2,
  'and': 3, '&': 3,
  'xor': 4, '^': 4,
  'slw': 5, '<<': 5,
  'srw': 6, '>>': 6,
  'rol': 7,
  'asr': 8,
  'fadds': 9,
  'fmuls': 10,
}
