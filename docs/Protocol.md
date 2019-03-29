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
BitScribe protocol is agnostic about how documents are encoded/decoded into a chunkset. (The 
library includes some default implementations though.) 

A **document hash** is the cryptographic hash derived from the blockchain's hasing primitive
(SHA256 for Bitcoin). A **document address** is the blockchain address determinstically derived
from the document's hash.

After being engraved into the blockchain, the user can reconstruct the original document
given:

* The document's hash
* Read access to the blockchain
* Chunk decoder algorithm used in the engraving

## Engravings

An **engraving**
