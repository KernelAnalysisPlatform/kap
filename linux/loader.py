# XXX: Now Static class is required by load_binary function
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.relocation import RelocationSection
from elftools.common.exceptions import ELFError
import struct

def get_arch(fb):
  if fb == 0x28:
    return 'arm'
  elif fb == 0xb7:
    return 'aarch64'
  elif fb == 0x3e:
    return 'x86-64'
  elif fb == 0x03:
    return 'i386'
  elif fb == 0x08:
    return 'mipsel'
  elif fb == 0x1400:   # big endian...
    return 'ppc'
  elif fb == 0x800:
    return 'mips'


def load_binary(static):
  try:
    elf = ELFFile(open(static.path))
  except ELFError:
    print "*** loader error: non-ELF detected"
    return
  # TODO: replace with elf['e_machine']
  progdat = open(static.path).read(0x20)
  fb = struct.unpack("H", progdat[0x12:0x14])[0]   # e_machine
  static['arch'] = get_arch(fb)
  static['entry'] = elf['e_entry']
  static.raw_binary = elf.get_section_by_name('.text').data()

  ncount = 0
  for section in elf.iter_sections():
    if static.debug >= 1:
      print "** found section", section.name, type(section)

    # relocatable module has no segment.
    if section.name == '.text':
      addr = static.load_address
      memsize = section['sh_size']
      static.add_memory_chunk(addr, section.data().ljust(memsize, "\x00"))
      #static.add_memory_chunk(addr, static.raw_binary.ljust(memsize, "\x00"))


      # hacks for PLT
      # TODO: this is fucking terrible
      if section.name == '.rel.plt' or section.name == '.rela.plt':
        # first symbol is blank
        plt_symbols = []
        for rel in section.iter_relocations():
          symbol = symtable.get_symbol(rel['r_info_sym'])
          plt_symbols.append(symbol.name)

        # does this change?
        PLT_ENTRY_SIZE = 0x10

        for section in elf.iter_sections():
          if section.name == ".plt":
            for name, addr in zip(plt_symbols,
                     range(section['sh_addr'] + PLT_ENTRY_SIZE,
                           section['sh_addr'] + PLT_ENTRY_SIZE + PLT_ENTRY_SIZE*len(plt_symbols),
                           PLT_ENTRY_SIZE)):
              static[addr]['name'] = name
            #print plt_symbols, section['sh_addr']
    elif isinstance(section, SymbolTableSection):
      for nsym, symbol in enumerate(section.iter_symbols()):
        if symbol['st_value'] != 0 and symbol.name != "" and symbol['st_info']['type'] == "STT_FUNC":
          # .text section
          if symbol['st_shndx'] == 2:
            static[static.load_address + symbol['st_value']]['name'] = symbol.name
            print symbol.name, hex(static.load_address + symbol['st_value'])

  if static.debug >= 1:
    print "** found %d names" % ncount


# test
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'KAP loader test')
    parser.add_argument('binary', help="path to the kernel module")
    args = parser.parse_args()

    class static:
        def __init__(self):
            self.path = args.binary
            self.debug = 1
            load_binary(self)
        def __setitem__(self, address, dat):
            pass
        def __getitem__(self, address):
            pass

    static()
