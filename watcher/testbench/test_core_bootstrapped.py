from fixtures import bootstrapped_env
from utils import run_watcher


import time


def test_block_600k(bootstrapped_env):
    """
    Test db state after including block 600k
    """
    db_conn, cfg_path = bootstrapped_env
    cp = run_watcher(cfg_path)
    assert cp.returncode == 0

    # Read db to verify state
    with db_conn.cursor() as cur:
        cur.execute("select height from core.headers order by 1 desc limit 1;")
        assert cur.fetchone()[0] == 600_000
        cur.execute("select count(*) from core.transactions;")
        assert cur.fetchone()[0] == 4
        cur.execute("select count(*) from core.outputs;")
        assert cur.fetchone()[0] == 12
        cur.execute("select count(*) from core.inputs;")
        assert cur.fetchone()[0] == 5
        cur.execute("select count(*) from core.data_inputs;")
        assert cur.fetchone()[0] == 1
        cur.execute("select count(*) from core.box_registers;")
        assert cur.fetchone()[0] == 3
        cur.execute("select count(*) from core.tokens;")
        assert cur.fetchone()[0] == 1
        cur.execute("select count(*) from core.box_assets;")
        assert cur.fetchone()[0] == 1
