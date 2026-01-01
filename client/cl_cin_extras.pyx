import struct
import numpy
cimport numpy as cnp
cimport cython

cnp.import_array()

"""
==================
Huff1Decompress
==================
"""
@cython.boundscheck(False)
@cython.wraparound(False)
def Huff1Decompress(
    in_blk: bytes,
    cnp.ndarray[cnp.uint8_t, ndim=3] hnodes1tree,
    cnp.ndarray[cnp.uint8_t, ndim=3] hnodes1vals,
    cnp.ndarray[cnp.uint8_t, ndim=3] hnodes1leaf,
    cnp.ndarray[cnp.uint8_t, ndim=1] numhnodes1,
) -> bytearray:  # cblock_t

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
	cdef unsigned int count = struct.unpack("<L", in_blk[:4])[0]
	cdef unsigned int input_offset = 0
	cdef bytes input_data = in_blk[4:]
	cdef bytearray out = bytearray(count)
	cdef unsigned int out_p = 0

	cdef unsigned int prevpixel = 0
	cdef unsigned int nodenum = numhnodes1[0]
	cdef unsigned int prevnodenum = 0
	cdef unsigned int nodeval = 0
	cdef unsigned int leaf = 0
	cdef unsigned int inbyte = 0
	cdef unsigned int i = 0

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
