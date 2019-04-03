# BitScribe Protocol

The BitScribe protocol is a method for permanetely engraving arbitrarily large amounts of 
data into the Bitcoin blockchain (or Bitcoin like blockchains). It describes a way to 
represent a single document across multiple transactions, and a method for recovering
that document using only the canonical blockchain. The protocol is designed to be highly 
resilient against forgers, censors, and other forms of motivated attacks.

## Documents, Engravings, and Blockchains

A **document** is the fundamental element of data. It represents any arbitrary peice of
standalone digital content. Although the term "document" is used, it can be multimedia,
executable binaries, filesystem image, or anything else. 

The **blockchain** is the pre-existing, canonical, distributed consensus ledger, whose
aggregate proof-of-work or other mining related barriers makes it next economically 
infeasible to alter blocks after they're committed. For the rest of this spec, we'll use
blockchain interchangeably with the Bitcoin blockchain. However this protocol can be 
applied to most other blockchains with relatively minimal modification. 

An **engraving** is the representation of a document on the blockchain. An **uploader 
writer** orchestrates his transactions to create an engraving on the blockchain in a way 
that can be read by any **reader clients** who can view the blockchain. A document can
have zero, one, or multiple engravings on a given blockchain. As long as at least one 
engraving is complete, reader clients can reconstruct the document.

## Document Address

A **document hash** is the cryptographic hash of the document using the blockchain's native 
hasing primitive (SHA256 for Bitcoin). A **document address** is the blockchain address 
determinstically derived from the document's hash. 

The document address is the canonical location of the document on the blockchain. No matter
where, when, by who, or how many times an engraving was made, a reader client simply needs
to know the hash of the data they want to read. As long as at least one engraving
exists the document can be deterministically reconstructed.

The address also serves as a way to prove authenticity, preventing forgeries, errors and spam
attacks. If an engraving is incorrect, either because of malice or error, then the hash of
its reconstruction will not match the address it maps to. In which case the client can discard
it, and find an authentic engraving (if any exist).

A **dimunitive address** is the address mapping to the first N-bits of the document hash.
The 92-bit dimunitive address is the address derived from the first 92-bits of the SHA256
hash, with the trailing bits set to 0. A 256-bit hash has 255 defined dimunitive addresses.

The purpose of dimunitive addresses are to allowed documents to be located and shared using
fewer number of bits. At the cost of potentially higher probability of collission. However
in the case of collission, the client can always query with more bits. 

## Chunks

Engravings divide a document's data up into **chunks**, which are sub-units of data small 
enough to fit within a single transaction. A chunk contains both a segment of data from the 
document as well as encoding metadata specific to that chunk.

A **chunk scheme** is metadata that describes how to encode and decode the document to and 
from individual chunks. Chunk schemes are one-to-one specific to individual engravings. 
Individual engravings can have different chunk schemes, even if they're representing the same
document. It's the responsibility of the reader client to scan the each engraving's chunk 
individual scheme when reconstructing the document. 

A document and chunk scheme uniquely and deterministically define a **chunk set**. All chunks
within a chunk are always unique. (Although the document segments themselves do not have to
be unique. The encoding metadata assures set uniqueness.) This property allows for individual
chunks to be duplicated in the engraving without requiring resolution or risking data 
corruption.

#### Fill in Chunk Scheme details

## Anchors

**Anchors** is how reader clients discover engravings (if any) from a document's address.
Engravings are references by an unspent transaction output (UTXO) at the document address.
(As a random cryptographic hash, UTXOs at the document address are permanetely unspendable.)

To find an engraving, the reader cliend follows the UTXO back to the candidate. Not all
candidates will be valid engravings. (Any blockchain user can send a transaction to the 
document address.) However by checking that the engraving structure is valid, and that
the engraving's hash matches the address, an authentic anchor (if any exist) will always
be recovered. Since the cost of blockchain writes are much higher than blockchain reads,
denial-of-service attacks by faking anchors in the blockchain is infeasible.

**Dimunitive Anchors** are the same concept as anchors, but the UTXO is sent to the 
document's dimunitive address. The UTXO making up the dimunitive anchor always occurs on
a transaction shared with a regular anchor. Reader clients must take care to verify that
the paired addresses represent a valid canonical/dimunitive pair, to avoid forgery attacks.

As long as an an anchor to an authentic engraving exists at the canonical document address,
this validates the dimunitive by definition. If the subset engraving hashes to the document's
hash, then the subset of bits will in turn hash to the dimunitive.

## Capstone Transaction

The transaction in the engraving that outputs the anchor is the **capstone transaction**. 
Using it a reader can determistically and in bounded time retrieve each chunk's constituent 
transaction. Capstone transactions must conform to a specific structure to be considered valid:

* Inputs - Complete set of root transactions for the scroll (see below) in the engraving. Must
  only contain ribbon root transactions. 
* First output - Any value sent to the document address
* Second output - Null data containing the metadata tag (defined below)
* Additional outputs - Ignored (but reserved for future protocol implementations, and
  therefore should not be included)

## Metadata Tag

The **metadata tag** is a byte string describing the version of the protocol used to make
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

* [N Chunks] (4 bytes) - Big endian integer of the total size of the chunk set. Since an engraving
  can contain duplicate transactions, the total number of chunk-containing transactions may
  be higher.
* [N Hops] (4 bytes) - Big endian integer of the number of transactions (chunk containing or not)
  contained in the entire engraving. Protocol only requires an upper bound, but implementations
  should try to make this equal or as tight as possible to the actual value.
* [Longest Chain] (4 bytes) - Big endian integer of the longest transaction path in engraving.
  Only required to be an upper bound, but implementations should make tight or equal to the
  actual value.

## Scroll and Cornerstones

The **scroll** is the bounded directed acycling graph (DAG) of transactions rooted at the capstone 
transaction. The scroll contains all chunks from the document's chunk set. Each chunk is represented
in the scroll by one or more **chunk transactions**. Any transaction in the scroll with null data in
the first ouput is by definition a chunk transction. The reader client adds its data to the chunk set
when reconstructing the document. Chunks may be duplicated on multiple transactions, and only one
copy should be included in the chunk set. Chunks may occur in any order in the scroll.

Any transaction in the scroll must only contain inputs from another transaction in the scroll or a
**cornerstone transaction**. A cornerstone transaction is a terminal node in the scroll's DAG, and
its input notes should not be processed. A cornerstone transaction is identified by any transaction
with null data in its last output containing the following big endian plaintext stamp 
`BitScribeCornerstone`

Any transaction in the scroll (including the roots and cornerstones) are **scroll nodes**. A scroll 
node may have input nodes to one or multiple scroll nodes. A scroll node must not have any non-scroll
inputs. A scroll node may have outputs to zero (if a root), one, or multiple scroll nodes. It may 
have outputs to one or more non-scroll transactions. Only the sequential inputs, starting at the
capstone transaction, should be read by the client when deciphering the scroll. Outputs should be
ignored (if they were in the scroll they'd be processed in the path to reaching that node).

When walking through the scroll, the read client should respect the size bounds set by the metadata tag.
If the longest path or total size of the transaction set exceeds the size bound the engraving should
be disregarded as invalid, without further processing. This prevents malicious traps where an attacker
creates a very very long scroll to penalize the cost of reading the document. The metadata tag lets the
read client know the size up front, and abandon the attempt if an error or attack violates that.

A scroll node may have outputs to two or more parent scroll nodes. In which case the read client will
reach it multiple times. For efficiency the read client should only process it once. (Duplicated
chunks should alwyas be safe, even if they occur on separate transactions). If multiple parents converge
to a single child, the child node and all grandchildren nodes should be considered only once when 
comparing to the metadata size bound.

## Write Efficiency

A large document requires a large number of chunk transactions. We want to reasonably tradeoff between
time and money efficiency to keep the engraving process efficient. The best way to do this is to 
sacrfice chunk write latency for in favor of chunk write bandwidth. Transaction fees are much lower if 
we're willing to accept high expected confirmation times. 

If chunks are sent in sequence this would result in very long times to write even small documents. 
Therefore the key is support writing a large number of blocks in parrallel. This allows us to set 
low transaction fees while keeping total completion time short.

The protocol supports this through two design choices. First chunk order does not matter. Therefore 
we're free to send chunk transactions as soon as we're ready, without dependency on completing any 
specific prior chunks. Second the DAG nature of the scroll supports committing transactions in 
parrallel, then merging them at the end. We can high an arbitrarily large number of threads 
committing blocks in parrallel at any given block confirmation.

## Attacks on Writes in Progress

One vector of attack is the possibility of corrupting the engraving while its being written. A 
malicious  attacker may observe the blockchain over time and an engraving attempt in real-time. As 
the chunks are written over time, the engraving may not finish until much later after the attempt 
is visible.

However the structure of the protocol prevents any outside user without access to the writer's 
private keys from corrupting the engraved structure. As long as the writer's transactions are 
accepted by the blockchain he can guarantee the ability to finish the engraving, even if the attempt
is publicly known before it even starts.

An engraving is just a collection of transaction series. As long as the writer makes each 
transaction in the  series output to an address under his control, then there's no way that a 
third party can alter the process. From the cornerstone to the signature at the document address, 
an engraving write attempt is secure if and only if the writer controls the UTXOs at each step. 

A third party can write forged or mal-formed engravings to the document address, in an attempt 
to muddle the ability to reconstruct the document. However the cost of blockchain reads is very 
cheap relative to blockchain writes. (And size bounds makes each engraving candidate read bounded 
in constant time.) So an attack like this would cost very much, for very minimal computation time 
costs to reader clients.
