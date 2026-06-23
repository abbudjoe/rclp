pub trait ReplayCache {
    /// Atomically record first use of `nonce`.
    ///
    /// Implementations must return `true` only when this call consumed a nonce
    /// that was not already present in the replay window. Production
    /// deployments should back this with shared durable storage; the verifier
    /// crate intentionally does not ship a process-local default cache.
    fn consume_nonce(&mut self, nonce: &str) -> bool;
}
