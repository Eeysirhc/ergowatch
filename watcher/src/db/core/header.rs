use crate::db::SQLArg;
use crate::db::SQLStatement;

pub const INSERT_HEADER: &str = "\
    insert into core.headers (height, id, parent_id, timestamp) \
    values ($1, $2, $3, $4);";

pub const DELETE_HEADER: &str = "\
    delete from core.headers where id = $1;";

pub struct HeaderRow<'a> {
    pub height: i32,
    pub id: &'a str,
    pub parent_id: &'a str,
    pub timestamp: i64,
}

impl HeaderRow<'_> {
    pub fn to_statement(&self) -> SQLStatement {
        SQLStatement {
            sql: String::from(INSERT_HEADER),
            args: vec![
                SQLArg::Integer(self.height),
                SQLArg::Text(String::from(self.id)),
                SQLArg::Text(String::from(self.parent_id)),
                SQLArg::BigInt(self.timestamp),
            ],
        }
    }
}

pub fn rollback_statement(header_id: &str) -> SQLStatement {
    SQLStatement {
        sql: String::from(DELETE_HEADER),
        args: vec![SQLArg::Text(String::from(header_id))],
    }
}
