
# Recovering Writes in Progress

This describes an optional extension to the BitScribe protocol. It allows for
an in-progress engraving to be resumed, at an arbitrarily later writer. Use or non-use
of this extension does not affect the ability of base protocol compliant clients to read 
completed engravings.

Write interruption poses no additional cost in terms of money or time. As long as the
previous writer was compliant with the protocol extension, any other writer can resume
the engraving with no coordination or shared state (other than pre-sharing the keys).

Large engravings may run over the course of an arbitrarily long number of blocks.
Compounded over the long (relative to computer clocks) time between blocks, writing
schemes need to be resillient against system failure. Keys are small and known ahead of time,
and can be easily and safely stored. The interrupted writer does not to sync any other
state to a distributed datastore. The resumption writer can recover everything needed to
finish the engraving from the blockchain.

The protocol extension is also resilient against multiple writers simultaneously executing.
This is a risk in a distributed context, because there's no failproof way to determine if
a previous writer writer has actually failed.

## Document Declaration

A **document declaration** is a committed transaction to the blockchain that marks an
in-progress engraving. A **declaration hash** is the cryptographic hash of the document,
offset with a universal declaration salt to differentiate from the base protocol's document
hash. A **declaration address** is the hash's address in the blockchain.

A document declaration is a transaction from the engraving's gas tank address (see below) to
the documenet declaration address. A declaration transaction contains a **declaration metadata**
bytestring at its first null data output. Declaration transactions must contain declaration
metadata. Properly formatted with the following fields:

* [Protocol Preamble] (17 Bytes) - Plaintext string "BigScribeProgExt"
* [Version Tag] (4 bytes) - Big endian integer indicating the major version of the base protocol
* [Extension Version Tag] (4 Bytes) - Big endian integer of the major version of the extension
* [Codec Tag] (6 Bytes) - Big endian string declaring the chunk codec used in the engraving
* [Reserved] (Remaining) - Left empty but reserved for future versions

Any resumption writer can find previous engraving attempts by checking the UTXOs at the
declaration address. (Since the address is a cryptographic random hash, transactions to it
are never spendable.)  A UTXO that meets the following criteria can be considered as a
candidate for a partially complete engraving.

* 1) The transaction contains has a correctly structured declaration metadata.
* 2) The transaction originates from an address controlled by the writer (otherwise
     the writer is incapable of continuing the engraving)

If both conditions are true, the writer can evaluate the candidate engraving to see if it
has the chance to resume work in progress. Attackers may attempt to obscure in progress
engravings by polluting the document declaration address with references to spurious engravings.
However a writer will only resume an engraving that matches his pre-existing keys. Since the
attacker does not share the writer's keys, third-party UTXOs are quickly filtered out of the
candidate set.

## Gas tank

The **gas tank** is a blockchain address under the control of the writer. There should be
exactly one gas tank per engraving. Even if interrupted and resumed by another instance the
same gas tank should continue to be used. The gas tank address should not be used for any
other purpose even after the engraving completes.

All coins used in the engraving should be deposited to the gas tank first. Coins can be
withdrawn during or after the engraving process. Withdrawal transactions from the gas tank
should not contain null data conflicting with tagged endorsement transactions. (See below)

Knowledge of the gas tank address is sufficient for a writer to completely recover, and then
continue, a partial engraving from a prior compatible writer. All the writer needs to save to
recover in the case of interruption is this value.

Spends from the gas tank should only be used to construct the engraving or withdrawal coins.
Since anyone can send transactions to the address, the protocol extension is resilient against
any outputs sent to the gas tank. Regardless of whether the output is spent or not.

## Ribbons

**Ribbons** are unique address that are used to commit chunk transactions to the blockchain.
The set of committed chunks is fully reocverable ust by knowing the set of addresses making
up all the ribbons.

**Dangling edges** are the UTXOs inside the ribbot set, which originate from the same or
another ribbon address, or the gas tank address. To read the previously committed chunks,
the recoverer uses the ribbon set to lookup the dangling edges. The dangling edges are then
read the same way a completed scroll is in the base protocol. Any chunks not collected by
this process can be considered uncommited.

Ribbon addresses should not be used for any other purpose than the specific engraving. They
should not be used for multiple engravings or subsequent engraving. They should not be used
for any purpose, even after the engraving completes.

Dangiling edges can share common transaction grandchildren without issue. Since chunks are
unique in the set and be duplicated in the base protocol, reading them twice won't affect
the reconstruction. Dangling edges should not be spent unless one of the following is
true

* It's part of a transaction with at least one output that will be a dangling edges
* Blockchain has confirmed a transaction with a dangling edge that covers all of the
   chunk transaction grandchildren.
* The capstone transaction has been confirmed on the blockchain.

## Cornerstone Transactions

The extension imposes some additional requirements on cornerstone transactions on top
of the base protocol. The additional structure allows us to recover the ribbon set of
an in-progress engraving.

First all cornerstones must contain at least one input from the gas tank address. This
verifies that the cornerstone was legitimately generated by the authorized writer. Thus
preventing attacks whereby fake cornersontes are constructed to corrupt the reconstruction
of the in-progress write.

Second the cornerstone transaction must include a **bookkeeping divot**, which is a change
output going back to the gas tank address. This exists so that clients can easily identify
prior cornerstone transactions by combing the UTXOs at the gas tank address. This won't affect
the final engraving, because the change output will not be put into the scroll's transaction DAG.

Clients can find all prior capstone transactions by checking for UTXOs in the gas tank which
originate from protocol valid capstone transactions. Which in addition include at least one
input from the gas tank. Non-matching UTXOs are ignored.

The ribbot set is queries as the set of all addresses for which one or more capstone
transactions send output to. A single ribbon can receive output from multiple capstones. No
chunk transactions should be made on a ribbon until one or more of its capstones is commited
to the blockchain. The gas tank address is explicitly excluded from the ribbot set (even though
each capstone sends it a bookeeping divot).

This imposes a third additional requirement. A capstone can have no outputs besides to ribbons
or the gas tank.

## Completed Engravings

When an engraving is complete, the writer can optionally clean up any unspent outputs at its
dangling edges or bookeeping divots. (It's not mandatory, but is encouraged to minimize
ecological impact on the blockchain's transaction graph.) Therefore an attempt to read a
completed engraving, as if it was in-progress may erroneously miss previously commited chunks.

Therefore any reconstruction client should check for a completed engraving using the read process
in the base protocol. An attempt marked at the declaration address can be correlated with a
finalization at the document address. Using the normal engraving read procesdure find any single
capstone in the scroll. The completed engraving and declaration attempt correspond if and only
if the capstone contains at least one input from the document declaration.

## Simultaneous Writes

The purpose of this extension is to allow for the total interruption, then resumption by a
separate writer instance. However due to the distributed nature of this problem, the protocol
extension must be resilient against simultaneous uncoordinated writers.

One scenario is two writers both trying to spend the same dangling edges in the ribbot set.
In this case the blockchain can only confirm one transaction. In the case of a spent transaction
by another instance, compatible implementations should re-pull the dangling edges for the ribbon
set from the latest block.

Another scenario is a ribbon added by one writer, but not recognized by the other. Worse case
is that the second writer will not recognize the chunks being commited on the new ribbon. This
results in chunks being duplicated on multiple transactions. Since the protocol supports
duplicated chunks in the scroll, the engraving will remain uncorrupted. However this wastes money
on duplicated transactions. Therefore its suggested that implementing writers periodically check
the gas tank for new cornerstones added by other instances.

A third scenario is a race condition in the creation of the capstone transaction. Capstone
transactions are only created when they map to a valid, fully constructed scroll. In this
case the document address will contain references to both engravings (which may have overlapping
structure). However the base protocol supports multiple engravings per document.

A corner case of the above is when the dangling edges are spent into a capstone transaction or
a newly created ribbon. The original writer when it reconstructs its ribbon set will see fewer
chunks than before. Since chunks can never be removed from the blockchain, this should trigger
a full reconstruction. First the document address should be checked to see if the engraving was
completed. If not, then the gas tank should be checked for new cornerstones.

A final possibility is that a simultaneous writer exists, but is corrupted. In this case a full
reconstruction might still yield a corrupted state. If detected the writer should re-start
the engraving from a new gas tank address. In the worse the base protocol is designed to arbitrate
corrupted engravings by checking the hash of the document. 
