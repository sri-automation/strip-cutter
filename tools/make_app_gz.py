"""Rebuild the copies of the control app after app/StripCutter.html changes.

  python tools/make_app_gz.py

  * index.html                                  - the online copy (GitHub Pages serves it)
  * firmware/StripCutterWiFi/app_gz.h           - the copy inside the Wi-Fi module (gzipped)

Then commit, and load the Wi-Fi sketch again so the machine serves the new app too.
"""
import hashlib, os, shutil, zlib, struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'app', 'StripCutter.html')
OUT_H = os.path.join(ROOT, 'firmware', 'StripCutterWiFi', 'app_gz.h')
OUT_INDEX = os.path.join(ROOT, 'index.html')


def gzip_bytes(data):
    """gzip with a fixed header (no time stamp), so the same HTML always gives the same bytes"""
    c = zlib.compressobj(9, zlib.DEFLATED, -15, 9)
    body = c.compress(data) + c.flush()
    head = b'\x1f\x8b\x08\x00' + b'\x00\x00\x00\x00' + b'\x02\x03'
    tail = struct.pack('<II', zlib.crc32(data) & 0xffffffff, len(data) & 0xffffffff)
    return head + body + tail


def main():
    html = open(SRC, 'rb').read()
    gz = gzip_bytes(html)
    tag = hashlib.sha256(html).hexdigest()[:16]
    lines = []
    for i in range(0, len(gz), 24):
        lines.append('  ' + ', '.join('0x%02x' % b for b in gz[i:i + 24]) + ',')
    lines[-1] = lines[-1].rstrip(',')
    text = ('// app_gz.h - the control app (StripCutter.html), gzipped. Made by make_app_gz.py; do not edit.\n'
            '// %d bytes of HTML -> %d bytes gzipped, sha256 %s\n'
            '#pragma once\n'
            '#define APP_ETAG "%s"\n'
            '#define APP_GZ_LEN %d\n'
            'static const uint8_t APP_GZ[] PROGMEM = {\n%s\n};\n') % (len(html), len(gz), tag, tag, len(gz), '\n'.join(lines))
    with open(OUT_H, 'w', newline='\n') as f:
        f.write(text)
    shutil.copyfile(SRC, OUT_INDEX)
    print('app %d bytes -> %d gzipped, etag %s' % (len(html), len(gz), tag))
    print('wrote', os.path.relpath(OUT_H, ROOT), 'and', os.path.relpath(OUT_INDEX, ROOT))


if __name__ == '__main__':
    main()
