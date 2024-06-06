import struct
import numpy
cimport numpy
cimport cython

"""
==================
Huff1Decompress
==================
"""
@cython.boundscheck(False)
@cython.wraparound(False)
def Huff1Decompress (in_blk: bytes, numpy.ndarray[numpy.uint8_t, ndim=3] hnodes1tree, 
	numpy.ndarray[numpy.uint8_t, ndim=3] hnodes1vals, 
	numpy.ndarray[numpy.uint8_t, ndim=3] hnodes1leaf, 
	numpy.ndarray[numpy.uint8_t, ndim=1] numhnodes1) -> bytearray: #cblock_t

	# Algorithm explained https://multimedia.cx/mirror/idcin.html

	"""
	byte *input;
	int nodenum;
	int count;
	cblock_t out;
	int inbyte;
	int *hnodes, *hnodesbase;
	"""

	# get decompressed count
	count: numpy.uint32_t = struct.unpack("<L", in_blk[:4])[0]
	input_offset: numpy.uint32_t = 0
	input_data: bytes = in_blk[4:]
	out: bytearray = bytearray(count)
	out_p: numpy.uint32_t = 0

	prevpixel: numpy.uint8_t = 0
	nodenum: numpy.uint8_t = numhnodes1[0]
	nodeval: numpy.uint8_t = 0
	leaf: numpy.uint8_t = 0
	inbyte: numpy.uint8_t = 0

	while count:
		# Read input byte
		if input_offset < len(input_data):
			inbyte = input_data[input_offset]
		else:
			inbyte = 0

		# Iterate over bits of input byte
		for i in range(8):

			if leaf:
			
				# Found leaf node of tree, getting pixel value
				out[out_p] = nodeval
				out_p += 1

				count -= 1
				if count==0:
					break
				
				# Change to root node of tree corresponding to previous pixel
				prevpixel = nodeval
				nodenum = numhnodes1[prevpixel]

			# Traverse down the tree to next node
			prevnodenum = nodenum
			nodenum = hnodes1tree[prevpixel, prevnodenum, inbyte & 1]
			nodeval = hnodes1vals[prevpixel, prevnodenum, inbyte & 1]
			leaf = hnodes1leaf[prevpixel, prevnodenum, inbyte & 1]
			inbyte >>= 1
		
		input_offset +=1
	
	if (input_offset+4 != len(in_blk)) and (input_offset+4 != len(in_blk) + 1):
	
		print("Decompression overread by {}".format((input_offset+4) - len(in_blk)))
	
	out = out[:out_p]
	assert len(out) == out_p

	return out

