use crate::db::SQLArg;
use crate::db::SQLStatement;

pub const INSERT_BOX_ASSET: &str = "\
    insert into core.box_assets (box_id, token_id, amount) \
    values ($1, $2, $3);";

pub struct BoxAssetRow<'a> {
    pub box_id: &'a str,
    pub token_id: &'a str,
    pub amount: i64,
}

impl BoxAssetRow<'_> {
    pub fn to_statement(&self) -> SQLStatement {
        SQLStatement {
            sql: String::from(INSERT_BOX_ASSET),
            args: vec![
                SQLArg::Text(String::from(self.box_id)),
                SQLArg::Text(String::from(self.token_id)),
                SQLArg::BigInt(self.amount),
            ],
        }
    }
}

pub mod constraints {
    pub const ADD_PK: &str = "alter table core.box_assets add primary key (box_id, token_id);";
    pub const NOT_NULL_BOX_ID: &str =
        "alter table core.box_assets alter column box_id set not null;";
    pub const NOT_NULL_TOKEN_ID: &str =
        "alter table core.box_assets alter column token_id set not null;";
    pub const FK_BOX_ID: &str = "alter table core.box_assets	add foreign key (box_id)
        references core.outputs (box_id)
        on delete cascade;";
    pub const CHECK_AMOUNT_GT0: &str = "alter table core.box_assets add check (amount > 0);";
}
