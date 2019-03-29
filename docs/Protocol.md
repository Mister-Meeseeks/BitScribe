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
with metadata related to the protocol version and chunk codec. Engravings can be uniquely
referenced by a single **capstone transaction** within the blockchain. A **signed engraving**
is an engraving whose capstone's first output is to the document address. 

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



