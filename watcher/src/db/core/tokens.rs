use super::sql::tokens::TokenRow;
use super::sql::tokens::TokenRowEIP4;
use super::BlockData;
use crate::db::SQLStatement;
use crate::parsing::Asset;
use crate::parsing::Output;
use log::warn;

// Handle newly minted tokes.
// New tokens have the same id as the first input box of the tx.
// New tokens can be minted into more than one asset record within the same box.
// New tokens can be minted into more than one output box.
// EIP-4 asset standard: https://github.com/ergoplatform/eips/blob/master/eip-0004.md
pub(super) fn extract_new_tokens(block: &BlockData) -> Vec<SQLStatement> {
    block
        .transactions
        .iter()
        .flat_map(|tx| {
            tx.outputs.iter().flat_map(|op| {
                op.assets
                    .iter()
                    .filter(|a| a.token_id == tx.input_box_ids[0])
                    .map(|a| Asset {
                        token_id: a.token_id,
                        amount: a.amount,
                    })
                    .reduce(|a, b| a + b)
                    .map(|a| match EIP4Data::from_output(op) {
                        Some(eip4_data) => TokenRowEIP4 {
                            token_id: &a.token_id,
                            box_id: op.box_id,
                            emission_amount: a.amount,
                            name: eip4_data.name,
                            description: eip4_data.description,
                            decimals: eip4_data.decimals,
                        }
                        .to_statement(),
                        None => TokenRow {
                            token_id: &a.token_id,
                            box_id: &op.box_id,
                            emission_amount: a.amount,
                        }
                        .to_statement(),
                    })
            })
        })
        .collect()
}

struct EIP4Data {
    name: String,
    description: String,
    decimals: i32,
}

impl EIP4Data {
    fn from_output<'a, 'b: 'a>(output: &'a Output) -> Option<EIP4Data> {
        if output.r4().is_none() || output.r5().is_none() || output.r6().is_none() {
            return None;
        }
        let r4 = output.r4().as_ref().unwrap();
        let r5 = output.r5().as_ref().unwrap();
        let r6 = output.r6().as_ref().unwrap();

        if r4.stype != "Coll[SByte]" || r5.stype != "Coll[SByte]" || r6.stype != "Coll[SByte]" {
            return None;
        }

        let decimals = match parse_eip4_register(&r6.rendered_value)
            .unwrap()
            .parse::<i32>()
        {
            Ok(i32) => i32,
            Err(error) => {
                warn!(
                    "Invalid integer literal in R6 of possible EIP4 transaction: {}. Box ID: {}",
                    &r6.rendered_value, &output.box_id
                );
                log::warn!("{}", error);
                return None;
            }
        };

        Some(EIP4Data {
            name: parse_eip4_register(&r4.rendered_value).unwrap(),
            description: parse_eip4_register(&r5.rendered_value).unwrap(),
            decimals: decimals,
        })
    }
}

fn parse_eip4_register(base16_str: &str) -> anyhow::Result<String> {
    let bytes = base16::decode(base16_str.as_bytes()).unwrap();
    anyhow::Ok(String::from_utf8(bytes)?)
}

#[cfg(test)]
mod tests {
    use super::extract_new_tokens;
    use crate::db;
    use crate::parsing::testing::block_600k;
    use crate::parsing::testing::block_minting_tokens;
    use crate::parsing::testing::block_multi_asset_mint;
    use pretty_assertions::assert_eq;

    #[test]
    fn block_without_minting_transactions() -> () {
        let statements = extract_new_tokens(&block_600k());
        assert_eq!(statements.len(), 0);
    }

    #[test]
    fn block_with_miniting_transactions() {
        let statements = extract_new_tokens(&block_minting_tokens());
        assert_eq!(statements.len(), 2);
        assert_eq!(statements[0].sql, db::core::sql::tokens::INSERT_TOKEN_EIP4);
        assert_eq!(statements[1].sql, db::core::sql::tokens::INSERT_TOKEN);
    }

    #[test]
    fn multi_asset_mint() {
        let statements = extract_new_tokens(&block_multi_asset_mint());
        assert_eq!(statements.len(), 1);
        assert_eq!(statements[0].sql, db::core::sql::tokens::INSERT_TOKEN);
        // Emission amount should be total of minting boxes
        assert_eq!(statements[0].args[2], db::SQLArg::BigInt(10 + 10));
    }
}
