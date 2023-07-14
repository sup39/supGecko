# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39

def cw_addr(ct, addr, po, endif=False):
  return (ct+0x10 if po else ct)<<24 | (addr+1 if endif else addr)&0x1ff_ffff
def cw_go(ct, if_, n):
  return ct<<24 | [True, False, None].index(if_)<<20 | n&0xffff

def parse_regop(ct, lhs, op, rhs):
  if op.endswith('='): op = op[:-1] # drop trailing =
  lhs, lhs_flag = parse_bracket_operand(lhs, 'lhs')
  rhs, rhs_flag = parse_bracket_operand(rhs, 'rhs')
  cw = ct<<24 | REGOP_IDX[op]<<20 | lhs_flag<<16 | rhs_flag<<17 | lhs&0xf
  return cw, rhs
def parse_regidx(ct, x, name):
  if x == 'ba': x = 0xf
  elif x == 'po': x = 0xf; ct |= 0x10
  else: x &= 0xf; assert x!=0xf, f'{name} cannot be F'
  return ct, x
def parse_bracket_operand(x, name): # returns (value, hasBracket)
  if type(x) == list:
    assert len(x)==1, f'`{name}` must be "x" or "[x]"'
    return x, 1
  return x, 0
def parse_binarg(x):
  return b''.join(map(parse_binarg, x)) if type(x)==list else \
    bytes.fromhex(x) if type(x)==str else \
      x.to_bytes(4, 'big') if type(x)==int else x

def make_asm_code(compile, input_path, raw, kwargs):
  if raw is not None: # raw code
    code = parse_binarg(raw)
    assert len(code)%4 == 0, \
      f'len(raw) should a multiple of 4, got {len(raw)}'
  else: # compile from file
    assert input_path is not None, 'either `input_path` or `raw` should be set'
    code, symbols = compile(input_path, **kwargs)
  return code
