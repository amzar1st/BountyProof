"""Small behavioral harness, not a GenVM/consensus/network emulator."""
import copy
import importlib.util
import sys
import types
from pathlib import Path
import pytest


@pytest.fixture
def env():
    class UserError(Exception):
        pass

    class Return:
        def __init__(self, calldata):
            self.calldata = calldata

    class Write:
        def __call__(self, fn):
            def transaction(self, *args, **kwargs):
                snapshot = copy.deepcopy(self.__dict__)
                try:
                    return fn(self, *args, **kwargs)
                except Exception:
                    self.__dict__.clear()
                    self.__dict__.update(snapshot)
                    raise
            return transaction
        payable = property(lambda self: self)

    class Contract:
        def __new__(cls):
            obj = super().__new__(cls)
            for name, kind in cls.__annotations__.items():
                setattr(obj, name, kind())
            return obj

    messages, transfers, responses, prompts = [], [], {}, []
    ctx = types.SimpleNamespace(sender_address="owner", contract_address="contract", value=0)
    raw = {"datetime": "2026-11-18T00:00:00+00:00"}

    def get(url, **kwargs):
        payload = responses.get(url)
        if payload is None:
            return types.SimpleNamespace(status=404, body=b"not found")
        import json
        return types.SimpleNamespace(status=200, body=(payload if isinstance(payload, str) else json.dumps(payload)).encode())

    def prompt(text):
        prompts.append(text)
        return e.answer

    def run(leader, validator):
        result = leader()
        e.validator = validator
        if not validator(Return(result)):
            raise UserError("validator disagreement")
        return result

    class Internal:
        def emit(self, **kwargs):
            assert kwargs == {"on": "finalized"}
            return self
        def finalize_verdict(self, attempt):
            messages.append(attempt)

    def interface(cls):
        class Bound:
            def __init__(self, address):
                self.address = address
            def emit_transfer(self, *, value, on="finalized"):
                assert on == "finalized"
                transfers.append((self.address, value))
        return Bound

    gl = types.SimpleNamespace(Contract=Contract, message=ctx, message_raw=raw,
         public=types.SimpleNamespace(write=Write(), view=lambda fn: fn),
         vm=types.SimpleNamespace(UserError=UserError, Return=Return, run_nondet_unsafe=run),
         evm=types.SimpleNamespace(contract_interface=interface), get_contract_at=lambda _: Internal(),
         nondet=types.SimpleNamespace(web=types.SimpleNamespace(get=get), exec_prompt=prompt))
    module = types.ModuleType("genlayer")
    module.gl, module.Address, module.u256 = gl, str, int
    sys.modules["genlayer"] = module
    spec = importlib.util.spec_from_file_location("bounty", Path(__file__).parents[1] / "contracts/bounty_proof.py")
    contract_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract_module)
    e = types.SimpleNamespace(m=contract_module, gl=gl, ctx=ctx, raw=raw, messages=messages,
                              transfers=transfers, responses=responses, prompts=prompts, answer="{}")
    e.contract = contract_module.BountyProof()
    e.now = e.contract._now()
    return e
