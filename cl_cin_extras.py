# Placeholder module for cl_cin_extras
import struct


def Huff1Decompress(in_blk, hnodes1tree, hnodes1vals, hnodes1leaf, numhnodes1):
	"""Pure Python Huffman decoder based on client/cl_cin_extras.pyx."""
	count = struct.unpack("<L", in_blk[:4])[0]
	input_offset = 0
	input_data = in_blk[4:]
	out = bytearray(count)
	out_p = 0

	prevpixel = 0
	nodenum = int(numhnodes1[0])
	nodeval = 0
	leaf = 0
	inbyte = 0

	while count:
		if input_offset < len(input_data):
			inbyte = input_data[input_offset]
		else:
			inbyte = 0

		for _ in range(8):
			if leaf:
				out[out_p] = nodeval
				out_p += 1
				count -= 1
				if count == 0:
					break

				prevpixel = nodeval
				nodenum = int(numhnodes1[prevpixel])

			prevnodenum = nodenum
			nodenum = int(hnodes1tree[prevpixel, prevnodenum, inbyte & 1])
			nodeval = int(hnodes1vals[prevpixel, prevnodenum, inbyte & 1])
			leaf = int(hnodes1leaf[prevpixel, prevnodenum, inbyte & 1])
			inbyte >>= 1

		input_offset += 1

	if (input_offset + 4 != len(in_blk)) and (input_offset + 4 != len(in_blk) + 1):
		print("Decompression overread by {}".format((input_offset + 4) - len(in_blk)))

	out = out[:out_p]
	assert len(out) == out_p

	return out
