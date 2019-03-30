# BitScribe Protocol

The BitScribe protocol is a method for permanetely engraving arbitrarily large amounts of 
data into the Bitcoin blockchain (or Bitcoin like blockchains). It describes a way to 
represent a single document across multiple transactions, and a method for recovering
that document using only the canonical blockchain. The protocol is designed to be highly 
resilient against forgers, censors, and other forms of motivated attacks.

## Documents and Chunks

The fundamental element of BitScribe are documents. A **document** is any standalone sequence 
of digital data. In practice BitScribe is optimized for documents between 1KB to 1MB in size. 
Smaller documents can be more practically written using a single transaction
(80 bytes in Bitcoin v0.12) or a small number of transactions with less representational
overhead. Support exists for documents up to 1 GB or 10 million transactions, but fully 
writing such large chunks of data would be impractical and costly in terms of time and
money. 

Documents are divisible into **chunks**, which are sub-units of data small enough to fit within
a single transaction. A document's **chunk set** is a unique set of individual chunks from which 
the document can be fully recovered. Chunk sets by definition cannot contain duplicate chunks.
The higher-layer protocol to encode/decode chunks into documents is the *chunk codec*. Bitscribe
protocol is agnostic about the chunk codec used. (The library includes some default implementations
though.)

A **document hash** is the cryptographic hash derived from the blockchain's hasing primitive
(SHA256 for Bitcoin). A **document address** is the blockchain address determinstically derived
from the document's hash.

After being engraved into the blockchain, the user can reconstruct the original document
given:

* The document's hash
* Read access to the blockchain
* Chunk decoder algorithm used in the engraving

## Engravings

An **engraving** is a deterministically recoverable representation of a chunk set along
with metadata related to the protocol version and chunk codec. Engravings can be retrieved
with reference to a single blockchain transaction. A **signed engraving** is an engraving whose
reference transaction's first output is to the document address. 

Signed engravings prevents forgeries, errors in the protocol or chunk codec mismatches. A user
reading a document can verify that the recovered document matches the signature. It also
allows us to canonically query a document regardless of when, where or if an engraving has
been made.

To do so the user takes the document hash, and checks the unspent transactions (if any)
at the document address. (The document address is the result of a cryptographic hash, and
therefore transactions at the address are all unspendable.) Going in chronological order
the user treats each transaction as a potential capstone and uses it to attempt to recover
the docuent.

If no transactions are present or no transactions are valid complete capstones, then the user
concludes that the document has not been engraved. If a forged engraving is presnet, its hash
won't match the address and can be discarded. If multiple valid engravings are present, then
the user simply uses the first valid one. This also allows for multiple engravings using different
chunk codecs. Since the engraving includes this metadata the user can use the available or most
efficient chunk codec.

## Keystone Transaction

The engraving's reference transaction is a **capstone transaction**. Using it a reader can
determistically and in bounded time retrieve each chunk's constituent transaction. Keystone
transactions must conform to a specific structure to be considered valid:

* Inputs - Comprehensive list of cornerstone transactions (defined below) and nothing
  other than cornerstone transactions.
* First output - Any value sent to the document address
* Second output - Null data containing the metadata tag (defined below)
* Additional outputs - Ignored (but reserved for future protocol implementations, and
  therefore should not be included)

## Metadata Tag

The *metadata tag* is a byte string describing the version of the protocol used to make
the engraving, the chunk codec, and the *size bounds* of the structure. The byte array
is structured as follows in Big Endian order:

* [BitScribe Preamble] (10 bytes) - Plaintext string "BitScribe" to indicate a BitScribe
  protocol based engraving.
* [Version Tag] (4 bytes) - Big endian integer indicating the major version of the
  protocol
* [Codec Tag] (6 bytes) - Big endian byte string declaring the chunk codec used in the
  engraving.
* [Size bounds] (12 bytes) - Declaration of the engraving's size (more below)
* [Reverved] (Remaining) - Left empty but reserved for futures versions of the protocol

The size bounds declare the total size of the engraving up front. This is to avoid
situations where due to error or attack the engraving is mal-formed. Without knowing
the size bounds it's possible that the engraving reader could contiue unbounded until
the end of the transaction web. With size bounds reader clients can terminate if they read
past the declared size without fully recovering the chunk set.

If a Sybil attacker tries to enter huge engravings to raise the cost of reads through
spurious engravings, then the reader client can try reading small engravigs first. Since
the size bounds are included on the capstone transaction, the cost of checking the size of a
the candidate is O(1). Since blockchain reads are much mucher cheaper than blockchain writes
this makes the attack cost of Sybil attacks on a document impractically high.

The following fields are included in the size bound field:

* N Chunks (4 bytes) - Big endian integer of the total size of the chunk set. Since an engraving
  can contain duplicate transactions, the total number of chunk-containing transactions may
  be higher.
* N Hops (4 bytes) - Big endian integer of the number of transactions (chunk containing or not)
  contained in the entire engraving. Protocol only requires an upper bound, but implementations
  should try to make this equal or as tight as possible to the actual value.
* Longest Chain (4 bytes) - Big endian integer of the longest transaction path in engraving.
  Only required to be an upper bound, but implementations should make tight or equal to the
  actual value.

## Cornerstone Transaction


