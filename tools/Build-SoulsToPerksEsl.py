#!/usr/bin/env python3
r"""
Build-SoulsToPerksEsl.py - authors SoulsToPerks.esp (an ESPFE), the Dragonstone's base record.

ONE new record, one master (Skyrim.esm), light-flagged:
    0x800  ACTI  STP_Dragonstone      FULL "Dragonstone", the vanilla RuinsDragonStone01.nif mesh

Nothing else. Since 1.0.7 the plugin places nothing and overrides no vanilla record - no CELL,
no WRLD, no REFR (the owner, 2026-10-25: a mod that edits the High Hrothgar courtyard or the
Tamriel worldspace record must never conflict with this one). Up to 1.0.6 the plugin carried a
placed reference (0x801) in HighHrothgarExterior01, and a placed reference cannot exist without
copies of its parent CELL and WRLD records; those copies were the whole conflict surface. The
DLL now places the stone itself when the courtyard cell loads (source/Dragonstone.cpp:
EnsureCourtyardStone - same position, rotation and 0.7 scale as 1.0.6's reference), and
recognises it by this base record. 0x801 stays unused so it is never reissued to something else.

The activator's shape (bounds, model, marker colour) follows the Dragonstone that Ish's Souls to
Perks placed at the Guardian Stones (design decision 2026-09-01: keep the Dragonstone as the
in-world activator, move it to High Hrothgar). The mesh is a vanilla Skyrim asset; nothing from
the original mod's files is packaged. No script, no quest, no globals, no message - the DLL
watches TESActivateEvent for this base object and opens its own exchange menu.

The plugin ships as SoulsToPerks.esp carrying only the light flag (ESPFE), so it sorts among the
ordinary plugins.

Usage:  python Build-SoulsToPerksEsl.py [out.esp]
"""
import struct, sys, os

FORM_VER = 44
NEW_ACTI = 0x01000800
NEXT_OBJECT = 0x802        # 0x801 was 1.0.6's placed reference; never reissued

ACTI_EDID = b'STP_Dragonstone\x00'
ACTI_OBND = bytes.fromhex('beffc7ff0000420039009b00')   # -66,-57,0 .. 66,57,155 (the mesh's bounds)
ACTI_FULL = b'Dragonstone\x00'
ACTI_MODL = b'Clutter\\Ruins\\DragonStone\\RuinsDragonStone01.nif\x00'
ACTI_MODT = bytes.fromhex('020000000000000000000000')
ACTI_PNAM = bytes.fromhex('cc4c3300')                   # marker colour
ACTI_FNAM = bytes.fromhex('0000')


def sub(sig, data):
    assert len(data) < 0x10000, sig
    return sig.encode() + struct.pack('<H', len(data)) + data


def rec(sig, formid, body, flags=0):
    return (sig.encode() + struct.pack('<I', len(body)) + struct.pack('<I', flags)
            + struct.pack('<I', formid) + struct.pack('<HHHH', 0, 0, FORM_VER, 0) + body)


def grup(label, gtype, payload):
    return (b'GRUP' + struct.pack('<I', len(payload) + 24) + label
            + struct.pack('<i', gtype) + b'\x00' * 8 + payload)


def build():
    acti_body = (sub('EDID', ACTI_EDID) + sub('OBND', ACTI_OBND) + sub('FULL', ACTI_FULL)
                 + sub('MODL', ACTI_MODL) + sub('MODT', ACTI_MODT)
                 + sub('PNAM', ACTI_PNAM) + sub('FNAM', ACTI_FNAM))
    agroup = grup(b'ACTI', 0, rec('ACTI', NEW_ACTI, acti_body))

    num_records = 2   # 1 record + 1 group, TES4 excluded
    hedr = struct.pack('<fiI', 1.7, num_records, NEXT_OBJECT)
    tes4_body = (sub('HEDR', hedr)
                 + sub('CNAM', b'ApocryphaRealm\x00')
                 + sub('SNAM', b'Souls to Perks - the Dragonstone activator. SoulsToPerks.dll places it at High Hrothgar at runtime.\x00')
                 + sub('MAST', b'Skyrim.esm\x00') + sub('DATA', b'\x00' * 8))
    tes4 = rec('TES4', 0, tes4_body, flags=0x00000200)   # Light only (ESPFE) - no ESM flag
    return tes4 + agroup


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'dist', 'SoulsToPerks.esp')
    blob = build()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'wb').write(blob)
    print('wrote %s (%d bytes; 1 record: ACTI 0x800; no CELL, WRLD or REFR)' % (os.path.abspath(out), len(blob)))
