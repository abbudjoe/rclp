use thiserror::Error;

#[derive(Debug, Error)]
pub enum VerifierError {
    #[error("json serialization failed: {0}")]
    Json(#[from] serde_json::Error),
    #[error("invalid hex signature: {0}")]
    Hex(#[from] hex::FromHexError),
    #[error("hmac verification failed")]
    InvalidMac,
}
