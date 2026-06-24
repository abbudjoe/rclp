use std::fs::{self, File, OpenOptions};
use std::io::{self, ErrorKind, Write};
use std::path::{Path, PathBuf};

use sha2::{Digest, Sha256};

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ReplayCacheDurability {
    NonDurable,
    DurableShared { store_id: String },
}

impl ReplayCacheDurability {
    pub fn is_durable(&self) -> bool {
        match self {
            Self::DurableShared { store_id } => !store_id.trim().is_empty(),
            Self::NonDurable => false,
        }
    }
}

pub trait ReplayCache {
    /// Describe whether this cache is acceptable for production verification.
    ///
    /// Non-durable process-local replay state is useful for tests only. The
    /// verifier fails closed unless this reports a durable/shared store.
    fn durability(&self) -> ReplayCacheDurability {
        ReplayCacheDurability::NonDurable
    }

    /// Atomically record first use of `nonce`.
    ///
    /// Implementations must return `true` only when this call consumed a nonce
    /// that was not already present in the replay window.
    fn consume_nonce(&mut self, nonce: &str) -> bool;
}

#[derive(Clone, Debug)]
pub struct FileReplayCache {
    store_dir: PathBuf,
}

impl FileReplayCache {
    pub fn new<P: AsRef<Path>>(store_dir: P) -> std::io::Result<Self> {
        let store_dir = store_dir.as_ref().to_path_buf();
        fs::create_dir_all(&store_dir)?;
        Ok(Self { store_dir })
    }

    pub fn store_dir(&self) -> &Path {
        &self.store_dir
    }

    fn nonce_path(&self, nonce: &str) -> PathBuf {
        let digest = Sha256::digest(nonce.as_bytes());
        self.store_dir.join(hex::encode(digest))
    }

    fn commit_nonce(&self, nonce: &str) -> io::Result<bool> {
        let path = self.nonce_path(nonce);
        let mut file = match OpenOptions::new().create_new(true).write(true).open(&path) {
            Ok(file) => file,
            Err(error) if error.kind() == ErrorKind::AlreadyExists => return Ok(false),
            Err(error) => return Err(error),
        };

        if let Err(error) = Self::write_and_sync_marker(&mut file, &self.store_dir, nonce) {
            let _ = fs::remove_file(path);
            return Err(error);
        }
        Ok(true)
    }

    fn write_and_sync_marker(file: &mut File, store_dir: &Path, nonce: &str) -> io::Result<()> {
        file.write_all(nonce.as_bytes())?;
        file.write_all(b"\n")?;
        file.sync_all()?;
        File::open(store_dir)?.sync_all()?;
        Ok(())
    }
}

impl ReplayCache for FileReplayCache {
    fn durability(&self) -> ReplayCacheDurability {
        ReplayCacheDurability::DurableShared {
            store_id: self.store_dir.display().to_string(),
        }
    }

    fn consume_nonce(&mut self, nonce: &str) -> bool {
        if nonce.trim().is_empty() || nonce.contains('\n') || nonce.contains('\r') {
            return false;
        }
        self.commit_nonce(nonce).unwrap_or(false)
    }
}
