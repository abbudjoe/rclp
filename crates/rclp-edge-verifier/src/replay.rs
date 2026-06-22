use std::collections::HashSet;

pub trait ReplayCache {
    fn seen(&self, nonce: &str) -> bool;
    fn mark_seen(&mut self, nonce: &str);
}

#[derive(Clone, Debug, Default)]
pub struct InMemoryReplayCache {
    seen_nonces: HashSet<String>,
}

impl InMemoryReplayCache {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_seen<I, S>(nonces: I) -> Self
    where
        I: IntoIterator<Item = S>,
        S: Into<String>,
    {
        Self {
            seen_nonces: nonces.into_iter().map(Into::into).collect(),
        }
    }
}

impl ReplayCache for InMemoryReplayCache {
    fn seen(&self, nonce: &str) -> bool {
        self.seen_nonces.contains(nonce)
    }

    fn mark_seen(&mut self, nonce: &str) {
        self.seen_nonces.insert(nonce.to_string());
    }
}
