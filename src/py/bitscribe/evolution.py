

# Describes the high-level state of a specific transaction as it relates to the
# Bitcoin network at a specific time.
class TxNetworkState:
    PENDING = 1
    SOFT_CONFIRMED = 2
    CONFIRMED = 3
    DEAD = 4

# State machine that ingests the fixed, possibly unreliable, status updates
# from the Bitcoin network for a specific transaction. Based on rules and
# parameters those updates evolve a "network state" over time. E.g. is the
# transaction confirmed/rejected/pending/etc?
class TxNetworkStateMachine:
    def __init__ (self, timeout=60, ):
        self._state = PENDING

    def state (self):
        return self._state
    
    def transmit (self, unix_epoch):
        pass

    def declineTransmit (self):
        pass
        
    def rejectResponse (self):
        pass

    def offNetwork (self, unix_epoch):
        pass

    def txReplaced (self):
        pass

    def undoReplaced (self):
        pass

    # Only call this on transactions lookups with 0 confirmed blocks 
    def inMempool (self, unix_epoch):
        pass

    def confirmBlock (self, n_blocks, unix_epoch):
        self._state = SOFT_CONFIRMED

    class InternalState:
        DEAD = 1
        PRE_TRANSMIT = 2
        MEMPOOL = 3
        REPLACED = 4
        SOFT_CONFIRMED = 5
        HARD_CONFIRMED = 6
        

# Use this class for unexpected state changes that we want to re-confirm
# multiple times before accepting.
class RetryTimeoutState:
    def __init__ (self, n_tries, timeout_secs):
        self._n_tries = n_tries
        self._timeout = timeout_secs
        self._nth_fail = 0

    def isDead (self):
        return self._nth_fail >= self._n_tries

    # Class state is inherently optimistic. One sign of life, even if previously
    # dead is enough for us to declare life.
    def alive (self, unix_epoch):
        self._nth_fail = 0
    
    # State is inherently optimistic. Caller has to fail multiple times
    # over a long-enough time range before we declare death.
    def fail (self, unix_epoch):
        if (self._nth_fail == 0):
            self._nth_fail = 1
            self._last_fail = unix_epoch
        elif (unix_epoch >= self._last_fail + self._timeout):
            self._nth_fail = self._nth_fail + 1
            self._last_tail = unix_epoch
        
