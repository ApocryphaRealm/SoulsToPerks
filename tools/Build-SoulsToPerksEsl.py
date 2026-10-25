#!/usr/bin/env python3
r"""
Build-SoulsToPerksEsl.py - authors SoulsToPerks.esp (an ESPFE), the placement carrier for Souls to Perks.

Two NEW records, one master (Skyrim.esm), light-flagged:
    0x800  ACTI  STP_Dragonstone      FULL "Dragonstone", the vanilla RuinsDragonStone01.nif mesh
    0x801  REFR  STP_DragonstoneRef   places 0x800 in the High Hrothgar courtyard
plus the two structurally-mandatory parent overrides (WRLD Tamriel, CELL HighHrothgarExterior01)
that a placed reference cannot exist without. No script, no quest, no globals, no message - the
DLL watches TESActivateEvent for this reference and opens its own exchange menu.

The activator's shape (bounds, model, marker colour, scale 0.7) follows the Dragonstone that
Ish's Souls to Perks placed at the Guardian Stones (design decision 2026-09-01: keep the
Dragonstone as the in-world activator, move it to High Hrothgar). The mesh is a vanilla Skyrim
asset; nothing from the original mod's files is packaged.

Placement (design decision 2026-09-01: High Hrothgar): the courtyard in front of the doors,
Tamriel cell HighHrothgarExterior01 (grid 13,-9, CELL 0x000096CC). Coordinates were read from
Skyrim.esm's own markers in that courtyard (HighHrothgarExteriorMeditationPatrolStart at
55054,-36007,23461 and the two exterior doors at x=52640), not guessed.

Parent overrides are rebuilt from the live masters at build time (Update.esm if it overrides the
record, else Skyrim.esm) so they always carry authoritative vanilla data. Both are FULL copies of
the winning vanilla record (the page-claims audit, 2026-10-25): until 1.0.7 the WRLD copy kept a
hand-picked list of subrecords and so dropped MHDT, the worldspace's max-height data that
Update.esm and every DLC master carry, which our override would have blanked whenever it won.
Now only two kinds of subrecord are left out, both on purpose:
    RNAM  large-reference lists. Each plugin carries only its own (Dragonborn.esm, the vanilla
          winner, has 368 bytes of them against Skyrim.esm's 1.35 MB), so the game combines
          them across plugins; this plugin places no large reference and carries none.
    OFST  Skyrim.esm's cell offset table - file positions inside Skyrim.esm, meaningless here.
FULL is written as plain text ("Skyrim") because the master's is a localised string id and this
plugin is not localised.

The plugin ships as SoulsToPerks.esp carrying only the light flag (ESPFE), so it sorts among the
ordinary plugins (1.0.5 renamed it and cleared the ESM flag with make-espfe.py; the generator now
writes that header itself).

Usage:  python Build-SoulsToPerksEsl.py [out.esp] [Data folder]
"""
import struct, zlib, sys, os

FORM_VER = 44
NEW_ACTI = 0x01000800
NEW_REFR = 0x01000801

ACTI_EDID = b'STP_Dragonstone\x00'
ACTI_OBND = bytes.fromhex('beffc7ff0000420039009b00')   # -66,-57,0 .. 66,57,155 (the mesh's bounds)
ACTI_FULL = b'Dragonstone\x00'
ACTI_MODL = b'Clutter\\Ruins\\DragonStone\\RuinsDragonStone01.nif\x00'
ACTI_MODT = bytes.fromhex('020000000000000000000000')
ACTI_PNAM = bytes.fromhex('cc4c3300')                   # marker colour
ACTI_FNAM = bytes.fromhex('0000')

REFR_EDID = b'STP_DragonstoneRef\x00'
REFR_SCALE = 0.7
# High Hrothgar courtyard: between the doors (x 52640) and the meditation spot (x 55054),
# south of the door axis (y -36096) so the path stays clear; ground height from the courtyard
# markers. Rotation faces the doors.
REFR_POS = (54700.0, -36600.0, 23461.0)
REFR_ROT = (0.0, 0.0, 1.5708)

WRLD_FID = 0x0000003C     # Tamriel
CELL_FID = 0x000096CC     # HighHrothgarExterior01, grid (13,-9)
BLOCK_LBL = bytes.fromhex('ffff0000')    # exterior block    (Y=-1, X=0)
SUBBLK_LBL = bytes.fromhex('feff0100')   # exterior subblock (Y=-2, X=1)

WRLD_DROP = {'RNAM', 'OFST'}   # see the docstring: every other subrecord is carried verbatim


def sub(sig, data):
    assert len(data) < 0x10000, sig
    return sig.encode() + struct.pack('<H', len(data)) + data


def rec(sig, formid, body, flags=0):
    return (sig.encode() + struct.pack('<I', len(body)) + struct.pack('<I', flags)
            + struct.pack('<I', formid) + struct.pack('<HHHH', 0, 0, FORM_VER, 0) + body)


def grup(label, gtype, payload):
    return (b'GRUP' + struct.pack('<I', len(payload) + 24) + label
            + struct.pack('<i', gtype) + b'\x00' * 8 + payload)


def parse_subs(body):
    out, q, ov = [], 0, None
    while q < len(body):
        sig = body[q:q + 4].decode('ascii')
        ln = struct.unpack_from('<H', body, q + 4)[0]
        q += 6
        if sig == 'XXXX':
            ov = struct.unpack_from('<I', body, q)[0]
            q += ln
            continue
        if ov is not None:
            ln, ov = ov, None
        out.append((sig, body[q:q + ln]))
        q += ln
    return out


def fetch(master_path, wanted):
    """Pull (record flags, decompressed body) for FormIDs out of a master; missing ones are absent."""
    data = open(master_path, 'rb').read()
    hs = struct.unpack_from('<I', data, 4)[0]
    found = {}

    def walk(a, b):
        q = a
        while q < b:
            s = data[q:q + 4]
            size = struct.unpack_from('<I', data, q + 4)[0]
            if s == b'GRUP':
                gt = struct.unpack_from('<i', data, q + 12)[0]
                if gt == 0 and data[q + 8:q + 12] != b'WRLD':
                    q += size
                    continue
                walk(q + 24, q + size)
                q += size
            else:
                flags, fid = struct.unpack_from('<II', data, q + 8)
                if fid in wanted and fid not in found:
                    body = data[q + 24:q + 24 + size]
                    if flags & 0x00040000:
                        body = zlib.decompress(body[4:])
                    found[fid] = (flags, body, os.path.basename(master_path))
                q += 24 + size

    walk(24 + hs, len(data))
    return found


def build(data_dir):
    src = {}
    for master in ('Update.esm', 'Skyrim.esm'):
        got = fetch(os.path.join(data_dir, master), {WRLD_FID, CELL_FID} - set(src))
        src.update(got)
    missing = {WRLD_FID, CELL_FID} - set(src)
    if missing:
        raise SystemExit('Could not find %s in the masters' % missing)

    wsubs = parse_subs(src[WRLD_FID][1])
    for need in ('MHDT', 'CNAM', 'DNAM', 'MNAM'):
        assert need in dict(wsubs), 'Tamriel from %s has no %s' % (src[WRLD_FID][2], need)
    wrld_body = b''
    for sig, val in wsubs:
        if sig in WRLD_DROP:
            continue
        if sig == 'FULL':
            assert len(val) == 4, 'Tamriel FULL is no longer a localised string id'
            val = b'Skyrim\x00'                                     # FULL is localised in the master
        wrld_body += sub(sig, val)

    cell_flags, cell_raw, cell_from = src[CELL_FID]
    cell_body, dropped = b'', []
    for sig, val in parse_subs(cell_raw):
        # A water type owned by Update.esm would drag Update.esm in as a second master.
        if sig == 'XCWT' and cell_from == 'Update.esm' and struct.unpack('<I', val)[0] >> 24 == 0x01:
            dropped.append(sig)
            continue
        cell_body += sub(sig, val)
    grid = struct.unpack_from('<ii', dict(parse_subs(cell_raw))['XCLC'])[:2]
    assert grid == (13, -9), grid
    assert (int(REFR_POS[0] // 4096), int(REFR_POS[1] // 4096)) == grid, 'placement is outside the cell'

    acti_body = (sub('EDID', ACTI_EDID) + sub('OBND', ACTI_OBND) + sub('FULL', ACTI_FULL)
                 + sub('MODL', ACTI_MODL) + sub('MODT', ACTI_MODT)
                 + sub('PNAM', ACTI_PNAM) + sub('FNAM', ACTI_FNAM))
    refr_body = (sub('EDID', REFR_EDID) + sub('NAME', struct.pack('<I', NEW_ACTI))
                 + sub('XSCL', struct.pack('<f', REFR_SCALE))
                 + sub('DATA', struct.pack('<6f', *REFR_POS, *REFR_ROT)))

    # TEMPORARY reference (group type 9) - a plain world object, same as the vanilla clutter around it.
    temp = grup(struct.pack('<I', CELL_FID), 9, rec('REFR', NEW_REFR, refr_body))
    child = grup(struct.pack('<I', CELL_FID), 6, temp)
    subblk = grup(SUBBLK_LBL, 5, rec('CELL', CELL_FID, cell_body, flags=cell_flags & ~0x00040000) + child)
    block = grup(BLOCK_LBL, 4, subblk)
    wchild = grup(struct.pack('<I', WRLD_FID), 1, block)
    wgroup = grup(b'WRLD', 0, rec('WRLD', WRLD_FID, wrld_body, flags=src[WRLD_FID][0] & ~0x00040000) + wchild)
    agroup = grup(b'ACTI', 0, rec('ACTI', NEW_ACTI, acti_body))

    num_records = 11   # 4 records + 7 groups, TES4 excluded
    hedr = struct.pack('<fiI', 1.7, num_records, 0x802)
    tes4_body = (sub('HEDR', hedr)
                 + sub('CNAM', b'ApocryphaRealm\x00')
                 + sub('SNAM', b'Souls to Perks - Dragonstone placement. All behaviour is in SoulsToPerks.dll.\x00')
                 + sub('MAST', b'Skyrim.esm\x00') + sub('DATA', b'\x00' * 8))
    tes4 = rec('TES4', 0, tes4_body, flags=0x00000200)   # Light only (ESPFE) - no ESM flag
    return tes4 + agroup + wgroup, dropped, cell_from


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'dist', 'SoulsToPerks.esp')
    # Discovered, not hard-coded (rule 4): SKYRIM_DATA, else the first MO2 Stock Game found.
    candidates = [os.environ.get('SKYRIM_DATA', ''), r'D:\Modlists\Njordlinger\Stock Game\Data',
                  r'C:\Modlists\Apostasy\Stock Game\Data']
    data_dir = sys.argv[2] if len(sys.argv) > 2 else next(
        (c for c in candidates if c and os.path.isfile(os.path.join(c, 'Skyrim.esm'))), candidates[1])
    blob, dropped, cell_from = build(data_dir)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'wb').write(blob)
    print('wrote %s (%d bytes; CELL parent from %s; dropped: %s)'
          % (os.path.abspath(out), len(blob), cell_from, dropped or 'nothing'))
