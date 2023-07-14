# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39

from .asm import compile
from .utils import *
from .consts import *

# TODO: assert range of arg
class Gecko():
  def __init__(self, compile_flags={}):
    self.code = bytearray()
    self.compile_flags = compile_flags
  def append(self, *payloads):
    self.code += b''.join(map(parse_binarg, payloads))
    return self
  def dump_txt(self, indent=''):
    if type(indent) == int: indent = ' '*indent
    return '\n'.join(
      indent+' '.join(self.code[j:j+4].hex().upper() for j in [i, i+4])
      for i in range(0, len(self.code), 8)
    )
  def compile(self, input_path, addr=None, **kwargs0):
    kwargs = {'extra_'+k: v for k, v in self.compile_flags.items()}
    for k, v in kwargs0.items():
      if type(v) == str: v = [v]
      kwargs[k] = kwargs[k] + v if k in kwargs else v
    return compile(input_path, addr, **kwargs)
  ''' 00 '''
  def write8(self, addr, val, count=1, po=False):
    return self.append(
      cw_addr(0x00, addr, po),
      ((count-1)&0xffff) << 16 | val&0xff,
    )
  ''' 02 '''
  def write16(self, addr, val, count=1, po=False):
    return self.append(
      cw_addr(0x02, addr, po),
      ((count-1)&0xffff) << 16 | val&0xffff,
    )
  ''' 04 '''
  def write32(self, addr, val, po=False):
    return self.append(
      cw_addr(0x04, addr, po),
      val & 0xffffffff,
    )
  ''' 06 '''
  def write_string(self, addr, payload, po=False):
    if type(payload) == str: payload = bytes.fromhex(payload)
    size = len(payload)
    rsize = size%8
    if rsize: payload += b'\x00'*(8-rsize)
    return self.append(cw_addr(0x06, addr, po), size, payload)
  ''' 08 '''
  def write_addr(self, addr, n, unit, val, addr_step, val_step, po=False):
    t = UNIT_IDX[unit]
    return self.append(
      cw_addr(0x08, addr, po),
      val,
      t<<28 | (n&0xfff)<<16 | (addr_step&0xffff),
      val_step & 0xffffffff,
    )
  ''' 20-27 '''
  def if32(self, addr, op, val, po=False, endif=False):
    ct = 0x20 | CMP_IDX[op]
    return self.append(
      cw_addr(ct, addr, po, endif),
      val & 0xffffffff,
    )
  ''' 28-2F '''
  def if16(self, addr, op, val, mask=-1, po=False, endif=False):
    ct = 0x28 | CMP_IDX[op]
    return self.append(
      cw_addr(ct, addr, po, endif),
      (~mask & 0xffff)<<16 | val & 0xffff,
    )
  ''' 4_TYZ '''
  def sl_bapo(self, action, target, op, addr, bapo=None, gr=None):
    cw = ({'ba': 0x40000, 'po': 0x48000}[target] \
       |  {'load': 0x00000, 'set': 0x02000, 'store': 0x04000} \
       |  {'+=': 0x00100, '=': 0}[op] \
       |  {'ba': 0x00010, 'po': 0x10010, None: 0}[bapo]
    ) << 12
    if action == 'store':
      assert op == '=', '`op` should be "=" when storing ba/po'
    if gr is not None:
      cw |= 0x1_000 | gr
    return self.append(cw, addr&0xffffffff)
  def load_ba(self, *args, **kwargs):
    return self.sl_bapo('load', 'ba', *args, **kwargs)
  def set_ba(self, *args, **kwargs):
    return self.sl_bapo('set', 'ba', *args, **kwargs)
  def store_ba(self, *args, **kwargs):
    return self.sl_bapo('store', 'ba', *args, **kwargs)
  def load_po(self, *args, **kwargs):
    return self.sl_bapo('load', 'po', *args, **kwargs)
  def set_po(self, *args, **kwargs):
    return self.sl_bapo('set', 'po', *args, **kwargs)
  def store_po(self, *args, **kwargs):
    return self.sl_bapo('store', 'po', *args, **kwargs)
  ''' 46, 4E '''
  def store_ncl(self, target, offset):
    ct = {'ba': 0x46, 'po': 0x4E}[target]
    return self.append(ct<<24 | offset&0xffff, 0)
  ''' 60 '''
  def set_repeat(self, n, p):
    return self.append(0x60<<24 | n&0xffff, p&0xf)
  ''' 62 '''
  def execute_repeat(self, p):
    return self.append(0x62<<24, p&0xf)
  ''' 64 '''
  def return_(self, p, if_=None):
    return self.append(cw_go(0x64, if_, n=0), p&0xf)
  ''' 66 '''
  def goto(self, n, p, if_=None):
    return self.append(cw_go(0x66, if_, n), p&0xf)
  ''' 68 '''
  def gosub(self, n, p, if_=None):
    return self.append(cw_go(0x68, if_, n), p&0xf)

  ''' 80 '''
  def set_reg(self, gr, op, addr, bapo=None):
    c = {'ba': 0x8001, 'po': 0x9001, None: 0x8000}[bapo] \
      | {'+=': 0x0010, '=': 0}[op]
    return self.append(c<<16 | gr&0xf, addr&0xffffffff)
  def load_reg(self, gr, addr, unit=None):
    c = {'ba': 0x8201, 'po': 0x9201, None: 0x8200}[bapo]
    u = UNIT_IDX[unit]
    return self.append(c<<16 | u<<20 | gr&0xf, addr&0xffffffff)
  def store_reg(self, gr, addr, unit=None, count=1):
    c = {'ba': 0x8401, 'po': 0x9401, None: 0x8400}[bapo]
    t = UNIT_IDX[unit]
    y = (count - 1) & 0xfff
    return self.append(
      c<<16 | t<<20 | y<<4 | gr&0xf,
      addr & 0xffffffff,
    )
  ''' 86 '''
  def reg_op_imm(self, lhs, op, rhs):
    cw, rhs = parse_regop(0x86, lhs, op, rhs)
    return self.append(cw, rhs & 0xffffffff)
  ''' 88 '''
  def reg_op_reg(self, lhs, op, rhs):
    cw, rhs = parse_regop(0x88, lhs, op, rhs)
    return self.append(cw, rhs & 0xf)
  '''
    [8A] (K, XXXXXXXX) <- N
    [8C] K <- (N, XXXXXXXX)
  '''
  def memcpy(self, dst, src, n):
    if type(src) == int:
      assert type(dst)==tuple and len(dst)==2, \
        '`dst` should be in form of "(K, XXXXXXXX)"'
      N = src&0xf
      K, off = dst
      ct, K = parse_regidx(0x8A, K)
    else:
      assert type(dst) == int, \
        '`dst` and `src` cannot be tuple at the same time'
      assert len(src)==2, '`src` should be in form of "(N, XXXXXXXX)"'
      ct = 0x8C
      N, off = src
      K = dst&0xf
      ct, N = parse_regidx(0x8C, N)
    return self.append(
      ct<<24 | (n & 0xffff)<<8 | N<<4 | K,
      off & 0xffffffff,
    )
  ''' A0-A7 '''
  def if16_reg(self, N, op, K, offset=None, mask=-1, endif=False):
    ct = 0xA0 | CMP_IDX[op]
    ctK, K = parse_regidx(ct, K)
    ctN, N = parse_regidx(ct, N)
    if K==0xf or N==0xf:
      assert offset is not None, '`offset` should be set if ba/po is used'
    else:
      offset = 0
    assert ctK == ctN, 'ba and po cannot be used at the same time'
    ct = ctN
    return self.append(
      cw_addr(ct, addr, po=False, endif=endif)
      (K<<28 | N<<24 | ~mask&0xffff),
    )
  ''' A8-AF '''
  def if16_cnt(self, cnt, op, val, reset_on_true, mask=-1, endif=False):
    T = (8 if reset_on_true else 0) + (1 if endif else 0)
    return self.append(
      (0xA8 | CMP_IDX[op])<<24 | (cnt&0xffff)<<4 | T,
      ~mask<<16 | val&0xffff,
    )
  ''' C0 '''
  def C0(self, input_path=None, raw=None, **kwargs):
    code = make_asm_code(self.compile, input_path, raw, kwargs)
    if len(code)%8 == 4: # pad code with blr
      code += b'\x4E\x80\x00\x20'
    return self.append(0xC000_0000, len(code)>>3, code)
  ''' C2 '''
  def C2(self, addr, input_path, raw=None, po=False, **kwargs):
    code = make_asm_code(self.compile, input_path, raw, kwargs)
    if len(code)%8 == 0: # pad code with nop
      code += b'\x60\x00\x00\x00'
    code += b'\x00\x00\x00\x00' # append 0
    return self.append(cw_addr(0xC2, addr, po), len(code)>>3, code)
  ''' C6 '''
  def branch(self, addr, dst, po=False):
    return self.append(cw_addr(0xC6, addr, po), dst&0xffffffff)
  ''' CC '''
  def onoff_switch(self):
    return self.append(0xCC00_0000, 0)
  ''' CE '''
  def addr_range_check(self, l, u, endif=False):
    return self.append(
      cw_addr(0xCE, 0, po, endif),
      (l&0xffff)<<16 | (u&0xffff),
    )
  ''' E0 '''
  def full_terminator(self, ba=0, po=0):
    return self.append(0xE000_0000, (ba&0xffff)<<16 | (po&0xffff))
  ''' E2 '''
  def endif(self, count=None, else_=False, ba=0, po=0):
    if count is None:
      if else_: count = 1
      else: return self.full_terminator(ba, po)
    return self.append(
      0xE200_0000 | (0x1_000_00 if else_ else 0) | count&0xff,
      (ba&0xffff)<<16 | (po&0xffff),
    )
  ''' F0 '''
  def end_of_code(self):
    return self.append(0xF000_0000, 0)

  ''' C Kit '''
  def c_kit(self, addr_code, input_path, entries, **kwargs):
    code, symbols = self.compile(input_path, addr_code, **kwargs)
    # 06
    self.write_string(addr_code, code, po=False)
    # 04/C6
    for addr_src, action, name in entries:
      assert name in symbols, f'symbol "{name}" is not found in the .text section of {input_path}'
      addr_dst = symbols[name]
      if action == 'b':
        self.branch(addr_src, addr_dst, po=False)
      elif action == 'bl':
        d_addr = addr_dst - addr_src
        assert -0x200_0000 <= d_addr < 0x200_0000, 'cannot bl from %08X to %08X'%(addr_src, addr_dst)
        inst = 0x4800_0001 | d_addr&0x3ff_fffc
        self.write32(addr_src, inst, po=False)
      else: assert False, '`action` should be "b" or "bl", got "{action}"'
    return self
