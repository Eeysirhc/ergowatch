//! # unspent
//!
//! Maintain set of unspent boxes.

// TODO undo pub once genesis refactoring is done
pub mod usp;

use crate::db::SQLStatement;
use crate::parsing::BlockData;
use usp::bootstrapping;
use usp::delete_spent_box_statement;
use usp::insert_new_box_statement;

/// Insert output boxes, then delete input boxes
pub fn prep(block: &BlockData) -> Vec<SQLStatement> {
    let mut sql_statements: Vec<SQLStatement> = block
        .transactions
        .iter()
        .flat_map(|tx| {
            tx.outputs
                .iter()
                .map(|op| insert_new_box_statement(op.box_id))
        })
        .collect();
    sql_statements.append(
        &mut block
            .transactions
            .iter()
            .flat_map(|tx| {
                tx.input_box_ids
                    .iter()
                    .map(|box_id| delete_spent_box_statement(box_id))
            })
            .collect(),
    );
    sql_statements
}

/// Insert input boxes, then delete output boxes
pub fn prep_rollback(block: &BlockData) -> Vec<SQLStatement> {
    let mut sql_statements: Vec<SQLStatement> = block
        .transactions
        .iter()
        .flat_map(|tx| {
            tx.input_box_ids
                .iter()
                .map(|box_id| insert_new_box_statement(box_id))
        })
        .collect();
    sql_statements.append(
        &mut block
            .transactions
            .iter()
            .flat_map(|tx| {
                tx.outputs
                    .iter()
                    .map(|op| delete_spent_box_statement(op.box_id))
            })
            .collect(),
    );
    sql_statements
}

pub fn prep_bootstrap(height: i32) -> Vec<SQLStatement> {
    vec![
        bootstrapping::insert_new_boxes_statement(height),
        bootstrapping::delete_spent_boxes_statement(height),
    ]
}

#[cfg(test)]
mod tests {
    use super::usp;
    use crate::db::SQLArg;
    use crate::parsing::testing::block_600k;

    /*
       Block 600k has x inputs:

       - eb1c4a582ba3e8f9d4af389a19f3bc6fa6759fd33956f9902b34dcd4a1d3842f
       - c739a3294d592377a131840d491bd2b66c27f51ae2c62c66be7bb41b248f321e
       - 6ca2a9d63f2f08663c09d99126ec1be7b65ce2e8f34e283c4d5af78485b47c91
       - 5c029ba7b1c67deedbd68878d02e5d7bb49b54943bc68fb5a30956a7a16224e4

       outputs:
       - 029bc1cb151aaef51c3678d2c74f3e82c9f4d197dd37e7a4eb73612f9da4f1f6
       - 6cb8ffe391838b627cb893c9b2027aa2a03f3a20455dd11e5ac903c7e4179ace
       - aa94183d21f9e8fee38d4f3326d2acf8258dd36e6dff38142fa93e633d01464d
       - 5c029ba7b1c67deedbd68878d02e5d7bb49b54943bc68fb5a30956a7a16224e4
       - 22adc6d1fd18e81da0ab9fa47bc389c5948780c98906c0ea3d812eba4ef17a33
       - 98d0271b7a29d62b672d8dd002e38b8cfbfc8e4055a637422b3e9d59cd6ff86d
    */

    #[test]
    fn check_prep_statements() -> () {
        let statements = super::prep(&block_600k());
        assert_eq!(statements.len(), 6 + 4);
        assert_eq!(statements[0].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[1].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[2].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[3].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[4].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[5].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[6].sql, usp::DELETE_SPENT_BOX);
        assert_eq!(statements[7].sql, usp::DELETE_SPENT_BOX);
        assert_eq!(statements[8].sql, usp::DELETE_SPENT_BOX);
        assert_eq!(statements[9].sql, usp::DELETE_SPENT_BOX);
    }

    #[test]
    fn check_rollback_statements() -> () {
        let statements = super::prep_rollback(&block_600k());
        assert_eq!(statements.len(), 4 + 6);
        assert_eq!(statements[0].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[1].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[2].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[3].sql, usp::INSERT_NEW_BOX);
        assert_eq!(statements[4].sql, usp::DELETE_SPENT_BOX);
        assert_eq!(statements[5].sql, usp::DELETE_SPENT_BOX);
        assert_eq!(statements[6].sql, usp::DELETE_SPENT_BOX);
        assert_eq!(statements[7].sql, usp::DELETE_SPENT_BOX);
        assert_eq!(statements[8].sql, usp::DELETE_SPENT_BOX);
        assert_eq!(statements[9].sql, usp::DELETE_SPENT_BOX);
    }

    #[test]
    fn check_bootstrap_statements() -> () {
        let statements = super::prep_bootstrap(600000);
        assert_eq!(statements.len(), 2);
        assert_eq!(
            statements[0].sql,
            usp::bootstrapping::INSERT_NEW_BOXES_AT_HEIGHT
        );
        assert_eq!(
            statements[1].sql,
            usp::bootstrapping::DELETE_SPENT_BOXES_AT_HEIGHT
        );

        assert_eq!(statements[0].args[0], SQLArg::Integer(600000));
        assert_eq!(statements[1].args[0], SQLArg::Integer(600000));
    }
}
