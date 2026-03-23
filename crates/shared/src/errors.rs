use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub enum Error {
    FetchError(String),
    ParseError(String),
    DatabaseError(String),
    Internal(String),
}
