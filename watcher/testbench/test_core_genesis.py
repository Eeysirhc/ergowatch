from fixtures import genesis_env
from utils import run_watcher


def test_first_block(genesis_env):
    """
    Check db state after including first block.

    Should contain first block and genesis boxes.
    """
    db_conn, cfg_path = genesis_env
    cp = run_watcher(cfg_path)
    assert cp.returncode == 0

    # Read db to verify state
    with db_conn.cursor() as cur:
        cur.execute("select height from core.headers order by 1 desc limit 1;")
        assert cur.fetchone()[0] == 1
        cur.execute("select count(*) from core.transactions;")
        assert cur.fetchone()[0] == 1 + 1  # 1 dummy genesis tx + 1 from 1st block
        cur.execute("select count(*) from core.outputs;")
        assert cur.fetchone()[0] == 3 + 2  # 3 genesis boxes + 2 from 1st block
        cur.execute("select count(*) from core.inputs;")
        assert cur.fetchone()[0] == 1

        # cur.execute("select count(*) from core.assets;")
        # assert cur.fetchone()[0] == 1
