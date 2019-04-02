
from bitscribe.tx_state import *
import pytest

@pytest.mark.parametrize("time_events,is_dead", [
    ([], False),
    ([(70, False)], False),
    ([(60, False), (120, False), (180, False)], True),
    ([(60, False), (120, True), (180, False)], False),
    ([(60, False), (120, True), (150, False), (179, False)], False),
    ([(60, False), (90, True), (120, False), (180, False)], False),
    ([(60, False), (120, False), (180, True)], False),
    ([(60, False), (120, False), (180, True), (240, False), (300, False)],
     False),
    ([(60, False), (120, False), (180, True), (240, False),
      (300, False), (360, False)], True),
    ([(60, False), (70, False), (80, True), (120, False), (130, False),
      (170, False)], False),
    ([(60, False), (120, False), (180, False), (200, True)], False),
    ([(60, False), (120, False), (180, False), (200, True),
      (240, False), (300, False)], False),
    ([(60, False), (120, False), (180, False), (200, True),
      (240, False), (300, False), (360, False)], True),
])
def test_retry_timeout (time_events, is_dead):
    sm = RetryTimeoutState(3, 60)
    for (time, is_success) in time_events:
        if (is_success):
            sm.alive(time)
        else:
            sm.fail(time)
    assert sm.isDead() == is_dead

def test_tx_state_init():
    assert TxNetworkStateMachine().state() == TxNetworkState.PENDING

def test_tx_state_transmit():
    sm = TxNetworkStateMachine()
    sm.transmit(0)
    assert sm.state() == TxNetworkState.PENDING

def test_tx_state_no_transmit():
    sm = TxNetworkStateMachine()
    sm.declineTrasmit()
    assert sm.state() == TxNetworkState.DEAD

def test_tx_state_reject():
    sm = TxNetworkStateMachine()
    sm.rejectResponse()
    assert sm.state() == TxNetworkState.DEAD
    
def test_tx_state_trasmit_timeouit():
    sm = TxNetworkStateMachine(transmit_timeout=60)
    sm.transmit(10)
    sm.offNetwork(69)
    assert sm.state() == TxNetworkState.PENDING
    sm.offNetwork(70)
    assert sm.state() == TxNetworkState.DEAD

def test_tx_state_mempool():
    sm = TxNetworkStateMachine()
    sm.transmit(0)
    sm.inMempool(0)
    assert sm.state() == TxNetworkState.PENDING

def test_tx_state_drop_out():
    sm = TxNetworkStateMachine(mempool_timeout=60, mempool_tries=2)
    sm.transmit(0)
    sm.inMempool(10)
    sm.offNetwork(20)
    assert sm.state() == TxNetworkState.PENDING
    sm.offNetwork(80)
    assert sm.state() == TxNetworkState.DEAD
    sm.inMempool(81)
    assert sm.state() == TxNetworkState.PENDING

def test_tx_state_replaced():
    sm = TxNetworkStateMachine()
    sm.transmit(0)
    sm.inMempool(0)
    sm.txReplaced()
    assert sm.state() == TxNetworkState.DEAD
    sm.undoReplaced()
    assert sm.state() == TxNetworkState.PENDING
    
def test_tx_state_confirm_replaced():
    sm = TxNetworkStateMachine()
    sm.transmit(0)
    sm.inMempool(0)
    sm.txReplaced()
    with pytest.raises(Exception):
        sm.confirmBlock(1, 0)

def test_tx_state_replace_confirmed():
    sm = TxNetworkStateMachine()
    sm.transmit(0)
    sm.inMempool(0)
    sm.confirmBlock(1, 0)
    with pytest.raises(Exception):
        sm.txReplaced()

def test_tx_state_confirm():
    sm = TxNetworkStateMachine(confirm_blocks=5)
    sm.transmit(0)
    for n in range(5):
        sm.confirmBlock(1, 0)
        assert sm.state() == TxNetworkState.SOFT_CONFIRMED \
            if n < 5 else TxNetworkState.CONFIRMED

def test_tx_state_idempotent_confirm():
    sm = TxNetworkStateMachine(confirm_blocks=5)
    sm.transmit(0)
    for n in range(5):
        sm.confirmBlock(2, 0)
        assert sm.state() == TxNetworkState.SOFT_CONFIRMED
    for n in range(5):
        sm.confirmBlock(7, 0)
        assert sm.state() == TxNetworkState.CONFIRMED    

def test_tx_state_confirm_reorg():
    sm = TxNetworkStateMachine(confirm_blocks=5,
                               reorg_timeout=60, reorg_tries=2)
    sm.transmit(0)
    sm.confirmBlock(5, 0)
    sm.confirmBlock(4, 0)
    assert sm.state() == TxNetworkState.CONFIRMED
    sm.confirmBlock(4, 60)
    assert sm.state() == TxNetworkState.SOFT_CONFIRMED

def test_tx_state_confirm_loss():
    sm = TxNetworkStateMachine(confirm_blocks=5,
                               reorg_timeout=60, reorg_tries=2)
    sm.transmit(0)
    sm.confirmBlock(3, 0)
    sm.inMempool(0)
    assert sm.state() == TxNetworkState.SOFT_CONFIRMED
    sm.inMempool(60)
    assert sm.state() == TxNetworkState.PENDING
    
def test_tx_state_rollback_step_down():
    sm = TxNetworkStateMachine(confirm_blocks=5,
                               reorg_timeout=60, reorg_tries=2,
                               mempool_timeout=60, mempool_tries=2)
    sm.confirmBlock(3, 0)
    sm.offNetwork(0)
    assert sm.state() == TxNetworkState.CONFIRMED
    sm.offNetwork(60)
    assert sm.state() == TxNetworkState.SOFT_CONFIRMED
    sm.offNetwork(120)
    assert sm.state() == TxNetworkState.PENDING
    sm.offNetwork(180)
    assert sm.state() == TxNetworkState.DEAD
