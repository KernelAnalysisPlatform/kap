# XXX: Now Static class is required by load_binary function
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.relocation import RelocationSection
from elftools.common.exceptions import ELFError
import struct

kernel_syms = []

def load_ksyms():
  ksyms = open('/tmp/qira_ksyms').readlines()
  for k in ksyms:
      kernel_syms[k.split(' ')[2]] = int(k.split(' ')[0], 16)

def search_symbol(symbol):
  if symbol in kernel_syms:
    return kernel_syms[symbol]
  return None

def link_mod(static, elf):
  load_ksyms()
  for section in elf.iter_sections():
    if isinstance(section, RelocationSection):
      symtable = elf.get_section(section['sh_link'])
      if symtable.is_null():
        continue

      for rel in section.iter_relocations():
        symbol = symtable.get_symbol(rel['r_info_sym'])
        if rel['r_offset'] != 0 and symbol.name != "":
          addr = search_symbol(symbol.name)
          print 'link %s' % symbol.name, hex(addr)
