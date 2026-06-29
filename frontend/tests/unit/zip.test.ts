import { describe, expect, it } from 'vitest'
import { createZip } from '@/lib/zip'

/** Read a little-endian uint32 at `offset` from a byte array. */
function u32(bytes: Uint8Array, offset: number): number {
  return (
    (bytes[offset] |
      (bytes[offset + 1] << 8) |
      (bytes[offset + 2] << 16) |
      (bytes[offset + 3] << 24)) >>>
    0
  )
}

describe('createZip', () => {
  it('produces a valid ZIP signature and end-of-central-directory record', async () => {
    const blob = createZip({ 'a.txt': 'hello', 'b/c.txt': 'world' })
    const bytes = new Uint8Array(await blob.arrayBuffer())

    // Starts with a local file header signature.
    expect(u32(bytes, 0)).toBe(0x04034b50)

    // Ends with the 22-byte end-of-central-directory record...
    const eocd = bytes.length - 22
    expect(u32(bytes, eocd)).toBe(0x06054b50)
    // ...recording both entries.
    expect(bytes[eocd + 10]).toBe(2)
  })

  it('handles an empty file map', async () => {
    const blob = createZip({})
    const bytes = new Uint8Array(await blob.arrayBuffer())
    expect(bytes.length).toBe(22) // just the end-of-central-directory record
    expect(u32(bytes, 0)).toBe(0x06054b50)
  })
})
