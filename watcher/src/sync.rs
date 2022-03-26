use log::debug;
use log::error;
use log::info;
use log::warn;
use std::{thread, time};

use crate::db;
use crate::parsing::BlockData;
use crate::session::Session;

// TODO: move this to config
const POLL_INTERVAL_SECONDS: u64 = 5;

/// Sync db and track node in infinite loop
pub fn sync_and_track(session: &mut Session) -> Result<(), &'static str> {
    info!("Synchronizing with node");

    if session.db.is_empty().unwrap() {
        session.db.apply_constraints_all().unwrap();
        include_genesis_boxes(&session)?;
    };

    loop {
        let node_height = get_node_height_blocking(session);

        if node_height <= session.head.height {
            if session.exit_when_synced {
                debug!("Done syncing, exiting now");
                return Ok(());
            }
            debug!("No new blocks - waiting {} seconds", POLL_INTERVAL_SECONDS);
            thread::sleep(time::Duration::from_secs(POLL_INTERVAL_SECONDS));
            continue;
        }

        sync_to_height(session, node_height).unwrap();

        info!("Database is synced - waiting for next block");
    }
}

/// Sync db to given height
fn sync_to_height(session: &mut Session, node_height: u32) -> Result<(), &'static str> {
    while session.head.height < node_height {
        let next_height = session.head.height + 1;
        // Fetch next block from node
        let block = session.node.get_main_chain_block_at(next_height).unwrap();

        if block.header.parent_id == session.head.header_id {
            info!(
                "Including block {} for height {}",
                block.header.id, block.header.height
            );

            let prepped_block = BlockData::new(&block);
            include_block(session, &prepped_block);

            // Move head to latest block
            session.head.height = next_height;
            session.head.header_id = block.header.id;
        } else {
            // New block is not a child of last processed block, need to rollback.
            warn!(
                "Rolling back block {} at height {}",
                session.head.header_id, session.head.height
            );

            // Rollbacks may rely on database constraints to propagate.
            // So prevent any rollbacks if constraints haven't been set.
            if !session.allow_rollbacks {
                warn!("Preventing a rollback on an unconstrained database.");
                return Err("Preventing a rollback on an unconstrained database.");
            }

            // Retrieve processed block from node
            let block = session.node.get_block(&session.head.header_id).unwrap();

            // Collect rollback statements, in reverse order
            let prepped_block = BlockData::new(&block);
            rollback_block(session, &prepped_block);

            // Move head to previous block
            session.head.height = block.header.height - 1;
            session.head.header_id = block.header.parent_id;
        }
    }
    Ok(())
}

/// Add genesis boxes to database
fn include_genesis_boxes(session: &Session) -> Result<(), &'static str> {
    info!("Retrieving genesis boxes");
    let boxes = match session.node.get_genesis_blocks() {
        Ok(boxes) => boxes,
        Err(e) => {
            error!("{}", e);
            return Err("Failed to retrieve genesis boxes from node");
        }
    };
    let mut sql_statements = vec![];
    sql_statements.append(&mut db::core::genesis::prep(boxes));
    sql_statements.append(&mut db::unspent::prep_bootstrap(0));
    sql_statements.append(&mut db::balances::prep_bootstrap(0));
    session.db.execute_in_transaction(sql_statements).unwrap();
    Ok(())
}

/// Process block data into database
fn include_block(session: &Session, block: &BlockData) {
    // Prepare statements
    let mut sql_statements = db::core::prep(block);
    sql_statements.append(&mut db::unspent::prep(block));
    sql_statements.append(&mut db::balances::prep(block));

    // Execute statements in single transaction
    session.db.execute_in_transaction(sql_statements).unwrap();
}

/// Discard block data from database
fn rollback_block(session: &Session, block: &BlockData) {
    // Collect rollback statements, in reverse order
    let mut sql_statements: Vec<db::SQLStatement> = vec![];
    sql_statements.append(&mut db::balances::prep_rollback(block));
    sql_statements.append(&mut db::unspent::prep_rollback(block));
    sql_statements.append(&mut db::core::prep_rollback(block));

    // Execute statements in single transaction
    session.db.execute_in_transaction(sql_statements).unwrap();
}

/// Get latest block height from node.
/// Keeps trying until node is responsive.
fn get_node_height_blocking(session: &Session) -> u32 {
    loop {
        match session.node.get_height() {
            Ok(h) => return h,
            Err(e) => {
                error!("{}", e);
                info!("Retrying in {} seconds", POLL_INTERVAL_SECONDS);
                thread::sleep(time::Duration::from_secs(POLL_INTERVAL_SECONDS));
                continue;
            }
        };
    }
}

pub mod bootstrap {
    use super::get_node_height_blocking;
    use crate::db;
    use crate::parsing::BlockData;
    use crate::session::Session;
    use log::info;

    pub fn phase_1(session: &mut Session) -> Result<(), &'static str> {
        if !session.db.has_genesis_boxes() {
            super::include_genesis_boxes(session)?;
        }
        sync_core(session)?;
        session.db.apply_constraints_tier1().unwrap();
        Ok(())
    }

    pub fn phase_2(session: &mut Session) -> Result<(), &'static str> {
        expand_db(session)?;
        session.db.apply_constraints_tier2().unwrap();
        Ok(())
    }

    /// Sync core tables only.
    fn sync_core(session: &mut Session) -> Result<(), &'static str> {
        info!("Bootstrapping step 1/2 - syncing core tables");
        loop {
            let node_height = get_node_height_blocking(session);
            if node_height <= session.head.height {
                break;
            }
            sync_core_to_height(session, node_height)?;
        }
        info!("Minimal sync completed");
        Ok(())
    }

    pub fn db_is_bootstrapped(session: &Session) -> bool {
        // Compare last height of derived tables.
        match session.db.get_bootstrap_height().unwrap() {
            Some(h) => h == session.head.height as i32,
            None => false,
        }
    }

    /// Phase 2 - Fill derived tables to match sync height of core tables.
    // TODO: rename to reflect association with tier2/phase2
    fn expand_db(session: &mut Session) -> Result<(), &'static str> {
        info!("Bootstrapping step 2/2 - populating secondary tables");
        // Set tier 1 db constraints if absent.
        // Constraints may already be set if bootstrap process got interrupted.
        let constraints_status = session.db.constraints_status().unwrap();
        assert_eq!(constraints_status.tier_2, false);
        if !constraints_status.tier_1 {
            session.db.apply_constraints_tier1().unwrap();
        } else {
            info!("Tier 1 constraints have already been set. Likely recovering from interrupted bootstrapping.")
        }

        // Get last height of derived tables
        let bootstrap_height: i32 = match session.db.get_bootstrap_height().unwrap() {
            Some(h) => h,
            None => -1, // Empty tables, next height should be genesis (i.e. 0)
        };

        // Iterate from session.head.height to core_height
        // Run queries for each block height
        for h in bootstrap_height + 1..session.head.height as i32 + 1 {
            info!("Processing block {}/{}", h, session.head.height);
            // Collect statements
            let mut sql_statements: Vec<db::SQLStatement> = vec![];
            sql_statements.append(&mut db::unspent::prep_bootstrap(h));
            sql_statements.append(&mut db::balances::prep_bootstrap(h));

            // Execute statements in single transaction
            session.db.execute_in_transaction(sql_statements).unwrap();
        }

        Ok(())
    }

    /// Sync db core to given height
    ///
    /// No rollback support.
    fn sync_core_to_height(session: &mut Session, node_height: u32) -> Result<(), &'static str> {
        while session.head.height < node_height {
            let next_height = session.head.height + 1;
            // Fetch next block from node
            let block = session.node.get_main_chain_block_at(next_height).unwrap();
            info!(
                "Bootstrapping block {} for height {}",
                block.header.id, block.header.height
            );

            let prepped_block = BlockData::new(&block);
            include_block(session, &prepped_block);

            // Move head to latest block
            session.head.height = next_height;
            session.head.header_id = block.header.id;
        }
        Ok(())
    }

    /// Process block data into database.
    /// Core tables only.
    fn include_block(session: &Session, block: &BlockData) {
        // Init parsing units
        let sql_statements = db::core::prep(block);

        // Execute statements in single transaction
        session.db.execute_in_transaction(sql_statements).unwrap();
    }
}
