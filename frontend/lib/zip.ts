/** Minimal, dependency-free ZIP writer (store / no compression).
 *
 * Enough to bundle a generated project's source files into a single .zip for
 * download. Stored (uncompressed) entries are valid ZIPs that GitHub, Vercel and
 * every unzip tool accept — source files don't need compression to be usable.
 */

function buildCrcTable(): Uint32Array {
  const table = new Uint32Array(256)
  for (let i = 0; i < 256; i++) {
    let c = i
    for (let k = 0; k < 8; k++) {
      c = (c & 1) === 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    }
    table[i] = c >>> 0
  }
  return table
}

const CRC_TABLE = buildCrcTable()

function crc32(bytes: Uint8Array): number {
  let crc = 0xffffffff
  for (let i = 0; i < bytes.length; i++) {
    crc = CRC_TABLE[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8)
  }
  return (crc ^ 0xffffffff) >>> 0
}

type Entry = { nameBytes: Uint8Array; size: number; crc: number; offset: number }

/** Build a ZIP archive from a `path -> contents` map. */
export function createZip(files: Record<string, string>): Blob {
  const encoder = new TextEncoder()
  const chunks: Uint8Array[] = []
  const entries: Entry[] = []
  let offset = 0

  const push = (bytes: Uint8Array): void => {
    chunks.push(bytes)
    offset += bytes.length
  }

  for (const [name, content] of Object.entries(files)) {
    const nameBytes = encoder.encode(name)
    const data = encoder.encode(content)
    const crc = crc32(data)
    const localOffset = offset

    const header = new DataView(new ArrayBuffer(30))
    header.setUint32(0, 0x04034b50, true) // local file header signature
    header.setUint16(4, 20, true) // version needed to extract
    header.setUint16(6, 0, true) // general purpose flags
    header.setUint16(8, 0, true) // compression method: 0 = store
    header.setUint16(10, 0, true) // last mod time
    header.setUint16(12, 0, true) // last mod date
    header.setUint32(14, crc, true)
    header.setUint32(18, data.length, true) // compressed size
    header.setUint32(22, data.length, true) // uncompressed size
    header.setUint16(26, nameBytes.length, true)
    header.setUint16(28, 0, true) // extra field length
    push(new Uint8Array(header.buffer))
    push(nameBytes)
    push(data)

    entries.push({ nameBytes, size: data.length, crc, offset: localOffset })
  }

  const centralStart = offset
  for (const entry of entries) {
    const record = new DataView(new ArrayBuffer(46))
    record.setUint32(0, 0x02014b50, true) // central directory signature
    record.setUint16(4, 20, true) // version made by
    record.setUint16(6, 20, true) // version needed
    record.setUint16(8, 0, true) // flags
    record.setUint16(10, 0, true) // compression
    record.setUint16(12, 0, true) // mod time
    record.setUint16(14, 0, true) // mod date
    record.setUint32(16, entry.crc, true)
    record.setUint32(20, entry.size, true) // compressed size
    record.setUint32(24, entry.size, true) // uncompressed size
    record.setUint16(28, entry.nameBytes.length, true)
    record.setUint16(30, 0, true) // extra length
    record.setUint16(32, 0, true) // comment length
    record.setUint16(34, 0, true) // disk number start
    record.setUint16(36, 0, true) // internal attributes
    record.setUint32(38, 0, true) // external attributes
    record.setUint32(42, entry.offset, true) // local header offset
    push(new Uint8Array(record.buffer))
    push(entry.nameBytes)
  }
  const centralSize = offset - centralStart

  const end = new DataView(new ArrayBuffer(22))
  end.setUint32(0, 0x06054b50, true) // end of central directory signature
  end.setUint16(4, 0, true) // disk number
  end.setUint16(6, 0, true) // central dir start disk
  end.setUint16(8, entries.length, true) // entries on this disk
  end.setUint16(10, entries.length, true) // total entries
  end.setUint32(12, centralSize, true)
  end.setUint32(16, centralStart, true)
  end.setUint16(20, 0, true) // comment length
  push(new Uint8Array(end.buffer))

  // Flatten into one ArrayBuffer-backed array (a definite `ArrayBuffer` view, so
  // it satisfies BlobPart regardless of the source arrays' buffer variance).
  const out = new Uint8Array(offset)
  let pos = 0
  for (const chunk of chunks) {
    out.set(chunk, pos)
    pos += chunk.length
  }
  return new Blob([out], { type: 'application/zip' })
}

/** Build a ZIP from `files` and trigger a browser download. */
export function downloadZip(filename: string, files: Record<string, string>): void {
  const url = URL.createObjectURL(createZip(files))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
