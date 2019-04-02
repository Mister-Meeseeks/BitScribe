
# Module for tracking and updating the last known state of specific transactions
# on the network over time.

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
    def __init__ (self, confirm_blocks=3, transmit_timeout=60,
                  mempool_timeout=120, mempool_tries=4,
                  reorg_timeout=300, reorg_tries=5):
        self._confirm_blocks = confirm_blocks
        self._transmit_timeout = transmit_timeout
        self._timeouts = self._initTimeouts((mempool_timeout, mempool_tries),
                                            (reorg_timeout, reorg_tries))
        self._state = self.State.PRE_TRANSMIT
        self._replaced = False

    @classmethod
    def _initTimeouts (cls, (mem_time, mem_tries), (reorg_time, reorg_tries)):
        return { cls.State.DEAD: RetryTimeoutState(0, 0),
                 cls.State.MEMPOOL: RetryTimeoutState(mem_time, mem_tries),
                 cls.State.SOFT_CONFIRMED: RetryTimeoutState(reorg_time,
                                                             reorg_tries),
                 cls.State.HARD_CONFIRMED: RetryTimeoutState(reorg_time,
                                                             reorg_tries) }
        
    def state (self):
        if (self._replaced):
            return TxNetworkState.DEAD
        else:
            return self._translate(self._state)

    @classmethod
    def _translate (cls, state):
        if (state <= cls.State.DEAD):
            return TxNetworkState.DEAD
        elif (state >= cls.HARD_CONFIRMED):
            return TxNetworkState.CONFIRMED
        elif (state == cls.SOFT_CONFIRMED):
            return TxNetworkState.SOFT_CONFIRMED
        else:
            return TXNetworkState.PENDING
                              
    def transmit (self, unix_epoch):
        self._transmit_time = unix_epoch
        self._state = self.State.IN_FLIGHT

    def declineTransmit (self):
        self._state = self.State.DEAD
        
    def rejectResponse (self):
        self._state = self.State.DEAD

    def offNetwork (self, unix_epoch):
        if (self._state in [self.State.PRE_TRANSMIT, self.State.DEAD]):
            pass
        elif (self._state == self.State.IN_FLIGHT):
            self._unreceived(unix_epoch)
        else:
            self._backtrack(unix_epoch)

    def _unreceived (self, unix_epoch):
        if (unix_epoch >= self._trasmit_time + self._transmit_timeout):
            self._state = self.State.DEAD

    def _backtrack (self, unix_epoch):
        self._getTimeout().fail(unix_epoch)
        if (self._timeout.isDead()):
            self._dropLevel()
            self._getTimeout.alive(unix_epoch) # Reset timeout...

    def _getTimeout (self):
        return self._timeouts[self._state]
            
    def _dropLevel (self):
        if (self._state == self.State.HARD_CONFIRM):
            self._state = self.State.SOFT_CONFIRM
        elif (self._state == self.State.SOFT_CONFIRM):
            self._state = self.State.MEMPOOL
        else:
            self._state = self.State.DEAD

    def txReplaced (self):
        pass

    def undoReplaced (self):
        pass

    # Only call this on transactions lookups with 0 confirmed blocks 
    def inMempool (self, unix_epoch):
        self._touchLevel(unix_epoch, self.State.MEMPOOL)

    def confirmBlock (self, n_blocks, unix_epoch):
        if (n_blocks < self._confirm_blocks):
            self._softConfirm(unix_epoch)
        else:
            self._hardConfirm(unix_epoch)

    def _softConfirm (self, unix_epoch):
        self._touchLevel(unix_epoch, self.State.SOFT_CONFIRM)

    def _hardConfirm (self, unix_epoch):
        self._touchLevel(unix_epoch, self.State.HARD_CONFIRM)

    def _touchLevel (self, unix_epoch, level):
        if (self._state > level):
            self._backtrack(unix_epoch)
        else:
            self._state = level
            self._getTimeout().alive(unix_epoch)
        
    class State:
        DEAD = 1
        PRE_TRANSMIT = 2
        IN_FLIGHT = 3
        MEMPOOL = 4
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
        
