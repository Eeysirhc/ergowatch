import pytest

from fixtures import fork_env, genesis_env
from fixtures import block_600k_env
from fixtures import token_minting_env
from fixtures import fork_env
from fixtures import unconstrained_db_env
from fixtures import bootstrap_empty_db_env


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


@pytest.mark.order(1)
class TestTokenMintingDB:
    def test_db_state(self, token_minting_env):
        """
        Check connection works and db is bootstrapped
        """
        with token_minting_env.db_conn.cursor() as cur:
            # Height is set to previous block
            cur.execute("select height from core.headers order by 1 desc limit 1;")
            assert cur.fetchone()[0] == 600_000

            # Single tx
            cur.execute("select count(*) from core.transactions;")
            assert cur.fetchone()[0] == 1

            # Always at least one
            cur.execute("select count(*) from core.outputs;")
            assert cur.fetchone()[0] == 1

            # No inputs (impossible in real life, but ok here)
            cur.execute("select count(*) from core.inputs;")
            assert cur.fetchone()[0] == 0

            # No data-inputs
            cur.execute("select count(*) from core.data_inputs;")
            assert cur.fetchone()[0] == 0

            # 1 pre-existing token
            cur.execute("select count(*) from core.tokens;")
            assert cur.fetchone()[0] == 0

            # No assets
            cur.execute("select count(*) from core.box_assets;")
            assert cur.fetchone()[0] == 0


@pytest.mark.order(1)
class TestForkDB:
    def test_db_state(self, fork_env):
        """
        Check connection works and db is bootstrapped
        """
        with fork_env.db_conn.cursor() as cur:
            # Height is set to previous block
            cur.execute("select height from core.headers order by 1 desc limit 1;")
            assert cur.fetchone()[0] == 672_219

            # Single tx
            cur.execute("select count(*) from core.transactions;")
            assert cur.fetchone()[0] == 1

            # 2 pre-existing outputs (1 for a minted token, one for a data-input)
            cur.execute("select count(*) from core.outputs;")
            assert cur.fetchone()[0] == 1

            # No inputs (impossible in real life, but ok here)
            cur.execute("select count(*) from core.inputs;")
            assert cur.fetchone()[0] == 0

            # No data-inputs
            cur.execute("select count(*) from core.data_inputs;")
            assert cur.fetchone()[0] == 0

            # No pre-existing token
            cur.execute("select count(*) from core.tokens;")
            assert cur.fetchone()[0] == 0

            # No assets
            cur.execute("select count(*) from core.box_assets;")
            assert cur.fetchone()[0] == 0


@pytest.mark.order(1)
class TestUnconstrainedDB:
    def test_db_state(self, unconstrained_db_env):
        """
        Check connection works and db is bootstrapped
        """
        with unconstrained_db_env.db_conn.cursor() as cur:
            # Height is set to previous block
            cur.execute("select height from core.headers order by 1 desc limit 1;")
            assert cur.fetchone()[0] == 672_219

            # Single tx
            cur.execute("select count(*) from core.transactions;")
            assert cur.fetchone()[0] == 1

            # 2 pre-existing outputs (1 for a minted token, one for a data-input)
            cur.execute("select count(*) from core.outputs;")
            assert cur.fetchone()[0] == 1

            # No inputs (impossible in real life, but ok here)
            cur.execute("select count(*) from core.inputs;")
            assert cur.fetchone()[0] == 0

            # No data-inputs
            cur.execute("select count(*) from core.data_inputs;")
            assert cur.fetchone()[0] == 0

            # No pre-existing token
            cur.execute("select count(*) from core.tokens;")
            assert cur.fetchone()[0] == 0

            # No assets
            cur.execute("select count(*) from core.box_assets;")
            assert cur.fetchone()[0] == 0

    def test_db_constraints_not_set(self, unconstrained_db_env):
        """
        Check db constraints are not set.
        """
        with unconstrained_db_env.db_conn.cursor() as cur:
            # Height is set to previous block
            cur.execute(
                "insert into core.headers (height, id, parent_id, timestamp) values (1, 'header', 'header', 123456789);"
            )
            cur.execute(
                "insert into core.headers (height, id, parent_id, timestamp) values (1, 'header', 'header', 123456789);"
            )


@pytest.mark.order(1)
class TestBootstrapEmptyDB:
    def test_db_state(self, bootstrap_empty_db_env):
        """
        Check db is empty
        """
        with bootstrap_empty_db_env.db_conn.cursor() as cur:
            # No headers
            cur.execute("select count(*) from core.headers;")
            assert cur.fetchone()[0] == 0

            # No tx
            cur.execute("select count(*) from core.transactions;")
            assert cur.fetchone()[0] == 0

            # No outputs
            cur.execute("select count(*) from core.outputs;")
            assert cur.fetchone()[0] == 0

            # No inputs
            cur.execute("select count(*) from core.inputs;")
            assert cur.fetchone()[0] == 0

            # No data-inputs
            cur.execute("select count(*) from core.data_inputs;")
            assert cur.fetchone()[0] == 0

            # No pre-existing token
            cur.execute("select count(*) from core.tokens;")
            assert cur.fetchone()[0] == 0

            # No assets
            cur.execute("select count(*) from core.box_assets;")
            assert cur.fetchone()[0] == 0
