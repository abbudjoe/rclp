use hmac::{Hmac, Mac};
use sha2::Sha256;

use crate::canonical_json::canonical_json;
use crate::errors::VerifierError;
use crate::types::CapabilityLeaseClaims;

pub const DEV_HMAC_SHA256_ALG: &str = "RCLP-DEV-HMAC-SHA256";

type HmacSha256 = Hmac<Sha256>;

pub fn verify_dev_hmac_sha256(
    claims: &CapabilityLeaseClaims,
    signature_hex: &str,
    secret: &str,
) -> Result<(), VerifierError> {
    let signature = hex::decode(signature_hex)?;
    let payload = canonical_json(claims)?;
    let mut mac =
        HmacSha256::new_from_slice(secret.as_bytes()).map_err(|_| VerifierError::InvalidMac)?;
    mac.update(payload.as_bytes());
    mac.verify_slice(&signature)
        .map_err(|_| VerifierError::InvalidMac)
}
