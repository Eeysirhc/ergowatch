from pathlib import Path
from collections import namedtuple

import pytest
import psycopg as pg

from .api import MockApi
from .api import get_api_blocks
from .db import conn_str
from .db import TestDB
from .db import generate_bootstrap_sql
from .config import format_config

_MockEnv = namedtuple("MockEnv", ["db_conn", "cfg_path"])
MockEnv = lambda db_conn, cfg_path: _MockEnv(db_conn, str(cfg_path))


@pytest.fixture
def genesis_env(tmp_path):
    api = "genesis"
    mock_api = MockApi(api)
    with TestDB() as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            cfg_path = tmp_path / Path("genesis.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def genesis_unconstrained_env(tmp_path):
    api = "genesis"
    mock_api = MockApi(api)
    with TestDB(set_constraints=False) as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            cfg_path = tmp_path / Path("genesis.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def block_600k_env(tmp_path):
    api = "600k"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB() as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            with conn.cursor() as cur:
                cur.execute(generate_bootstrap_sql(blocks))
            conn.commit()
            cfg_path = tmp_path / Path("600k.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def token_minting_env(tmp_path):
    api = "token_minting"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB() as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            with conn.cursor() as cur:
                cur.execute(generate_bootstrap_sql(blocks))
            conn.commit()
            cfg_path = tmp_path / Path("token-minting.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def fork_env(tmp_path):
    api = "fork"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB() as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            with conn.cursor() as cur:
                cur.execute(generate_bootstrap_sql(blocks))
            conn.commit()
            cfg_path = tmp_path / Path("fork.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def unconstrained_db_env(tmp_path):
    api = "fork"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB(set_constraints=False) as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            with conn.cursor() as cur:
                cur.execute(generate_bootstrap_sql(blocks))
            conn.commit()
            cfg_path = tmp_path / Path("unconstrained-db.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def bootstrap_empty_db_env(tmp_path):
    api = "bootstrap"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB(set_constraints=False) as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            cfg_path = tmp_path / Path("bootstrap.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def balances_bootstrap_env(tmp_path):
    api = "balances"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB(set_constraints=False) as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            with conn.cursor() as cur:
                cur.execute(generate_bootstrap_sql(blocks))
            conn.commit()
            cfg_path = tmp_path / Path("balances.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def balances_env(tmp_path):
    api = "balances"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB() as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            with conn.cursor() as cur:
                cur.execute(generate_bootstrap_sql(blocks))
            conn.commit()
            cfg_path = tmp_path / Path("balances.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def balances_fork_env(tmp_path):
    api = "balances_fork"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB() as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            with conn.cursor() as cur:
                cur.execute(generate_bootstrap_sql(blocks))
                # Insert the inputs being spent.
                # If not included here, the spending will not be registered in the balances schemas
                # as there is no existing output in the db to retrieve spent value from.
                # Include 1 box for Gxd4hMRT, will consume all balance when spent.
                # Include 1 box for 9hEZyV3x, but fake a larger balance and diffs so that
                # not all balance is consumed (to test a difference scenario).
                cur.execute(
                    """
                    insert into core.outputs (box_id, tx_id, header_id, creation_height, address, index, value) values
                    (
                        '9b7ec02bd5b3d34d7de9ad36a05c16ea76b462250bd2bfaf70ea8009247ea52b', -- box id of Gxd4hMRT spent in block 698626
                        '4c6282be413c6e300a530618b37790be5f286ded758accc2aebd41554a1be308', -- default tx in db init
                        'aaf522f0d258fc3641a19f89e04a59f29d1b09f7c54c8788d4c0ba343b6f3a84', -- parent header of block 698626
                        698620, -- creation height,  doesn't matter
                        'Gxd4hMRT6Lbs5aptyP3Ad2rB5FQD1SbxAWZacB7JLsMiMyRa1zcpKCLnsbXkmnE9NoHLZUTMYSvRh6eLXRKStcQVPNeVkeix5PKbh4z77KZepfnYPpU8weXkxuVfYudo4LwumcwV7uUsoxdop7j35MfZByYndqCZZ3UrqkCmViZdHKexRmDnpRpijMUELKopRJW8LMa2aVrw71W4gL3R3TrvdrPxzEGYj2EQHS8T1ZBKnskrDGBpYgqJ3xTb52HSjsLw81zRwXnWqn51zD4njtjVKeK4xwKePLhzK1e4ggfLEubMiHtBMXY3vngrTLsvrpfw1Bzuu2Edp2LR7mT46rFW2AzrStQvhCmCzDhjdbJra6ikg2FdzN4o4qUZ6GTWKzesGVcYynRbYR', --address
                        0, --index
                        16531500000 --value
                    ),
                    (
                        '683f99811cdaebcc51f55f707abbc3fe236c327d3ea6a53d6291980af62c6fb0', -- box id of 9hEZyV3x spent in block 698626
                        '4c6282be413c6e300a530618b37790be5f286ded758accc2aebd41554a1be308', -- default tx in db init
                        'aaf522f0d258fc3641a19f89e04a59f29d1b09f7c54c8788d4c0ba343b6f3a84', -- parent header of block 698626
                        698620, -- creation height,  doesn't matter
                        '9hEZyV3xCHVqx6SzD9GiL8wFMu4WKSodeakK3uyX3KQ1rKKkSDr', --address
                        1, --index
                        5000000 --value
                    );
                    
                    insert into bal.erg (value, address) values
                        (16531500000, 'Gxd4hMRT6Lbs5aptyP3Ad2rB5FQD1SbxAWZacB7JLsMiMyRa1zcpKCLnsbXkmnE9NoHLZUTMYSvRh6eLXRKStcQVPNeVkeix5PKbh4z77KZepfnYPpU8weXkxuVfYudo4LwumcwV7uUsoxdop7j35MfZByYndqCZZ3UrqkCmViZdHKexRmDnpRpijMUELKopRJW8LMa2aVrw71W4gL3R3TrvdrPxzEGYj2EQHS8T1ZBKnskrDGBpYgqJ3xTb52HSjsLw81zRwXnWqn51zD4njtjVKeK4xwKePLhzK1e4ggfLEubMiHtBMXY3vngrTLsvrpfw1Bzuu2Edp2LR7mT46rFW2AzrStQvhCmCzDhjdbJra6ikg2FdzN4o4qUZ6GTWKzesGVcYynRbYR'),
                        -- twice the actual amount so the balance doesn't drop to zero when box is spent
                        (5000000 * 2, '9hEZyV3xCHVqx6SzD9GiL8wFMu4WKSodeakK3uyX3KQ1rKKkSDr');
                    
                    insert into bal.erg_diffs (height, address, tx_id, value) values
                    (
                        698620, -- height
                        'Gxd4hMRT6Lbs5aptyP3Ad2rB5FQD1SbxAWZacB7JLsMiMyRa1zcpKCLnsbXkmnE9NoHLZUTMYSvRh6eLXRKStcQVPNeVkeix5PKbh4z77KZepfnYPpU8weXkxuVfYudo4LwumcwV7uUsoxdop7j35MfZByYndqCZZ3UrqkCmViZdHKexRmDnpRpijMUELKopRJW8LMa2aVrw71W4gL3R3TrvdrPxzEGYj2EQHS8T1ZBKnskrDGBpYgqJ3xTb52HSjsLw81zRwXnWqn51zD4njtjVKeK4xwKePLhzK1e4ggfLEubMiHtBMXY3vngrTLsvrpfw1Bzuu2Edp2LR7mT46rFW2AzrStQvhCmCzDhjdbJra6ikg2FdzN4o4qUZ6GTWKzesGVcYynRbYR', --address
                        '4c6282be413c6e300a530618b37790be5f286ded758accc2aebd41554a1be308', -- default tx in db init
                        16531500000 --value
                    ),
                    (
                        698620, -- height
                        '9hEZyV3xCHVqx6SzD9GiL8wFMu4WKSodeakK3uyX3KQ1rKKkSDr', --address
                        '4c6282be413c6e300a530618b37790be5f286ded758accc2aebd41554a1be308', -- default tx in db init
                        5000000 * 2 --value
                    );
                """
                )
            conn.commit()
            cfg_path = tmp_path / Path("balances_fork.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def unspent_env(tmp_path):
    api = "600k"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB() as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            with conn.cursor() as cur:
                cur.execute(generate_bootstrap_sql(blocks))
                # Add 4 boxes spent in block 600k, so they can be deleted
                cur.execute(
                    """
                    insert into usp.boxes (box_id)
                    values
                        ('eb1c4a582ba3e8f9d4af389a19f3bc6fa6759fd33956f9902b34dcd4a1d3842f'),
                        ('c739a3294d592377a131840d491bd2b66c27f51ae2c62c66be7bb41b248f321e'),
                        ('6ca2a9d63f2f08663c09d99126ec1be7b65ce2e8f34e283c4d5af78485b47c91'),
                        ('5c029ba7b1c67deedbd68878d02e5d7bb49b54943bc68fb5a30956a7a16224e4');
                """
                )
            conn.commit()
            cfg_path = tmp_path / Path("unspent.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)


@pytest.fixture
def unspent_bootstrap_env(tmp_path):
    api = "600k"
    mock_api = MockApi(api)
    blocks = get_api_blocks(api)
    with TestDB(set_constraints=False) as db_name:
        with pg.connect(conn_str(db_name)) as conn:
            with conn.cursor() as cur:
                cur.execute(generate_bootstrap_sql(blocks))
            conn.commit()
            cfg_path = tmp_path / Path("unspent.toml")
            cfg_path.write_text(format_config(db_name))
            with mock_api:
                yield MockEnv(conn, cfg_path)
