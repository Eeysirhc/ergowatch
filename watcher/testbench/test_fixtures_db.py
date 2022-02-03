import pytest

from fixtures import genesis_env
from fixtures import block_600k_env


@pytest.mark.order(1)
class TestGenesisDB:
    def test_db_is_empty(self, genesis_env):
        """
        Check connection works and db is blank
        """
        with genesis_env.db_conn.cursor() as cur:
            cur.execute("select count(*) as cnt from core.headers;")
            row = cur.fetchone()
        assert row[0] == 0


@pytest.mark.order(1)
class Test600kDB:
    def test_db_state(self, block_600k_env):
        """
        Check connection works and db is bootstrapped
        """
        with block_600k_env.db_conn.cursor() as cur:
            # Height is set to previous block
            cur.execute("select height from core.headers order by 1 desc limit 1;")
            assert cur.fetchone()[0] == 599_999

            # Single tx
            cur.execute("select count(*) from core.transactions;")
            assert cur.fetchone()[0] == 1

            # 2 pre-existing outputs (1 for a minted token, one for a data-input)
            cur.execute("select count(*) from core.outputs;")
            assert cur.fetchone()[0] == 2

            # No inputs (impossible in real life, but ok here)
            cur.execute("select count(*) from core.inputs;")
            assert cur.fetchone()[0] == 0

            # No data-inputs
            cur.execute("select count(*) from core.data_inputs;")
            assert cur.fetchone()[0] == 0

            # 1 pre-existing token
            cur.execute("select count(*) from core.tokens;")
            assert cur.fetchone()[0] == 1

            # No assets
            cur.execute("select count(*) from core.box_assets;")
            assert cur.fetchone()[0] == 0
