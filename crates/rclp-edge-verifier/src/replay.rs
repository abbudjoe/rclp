use std::collections::HashSet;
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

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ReplayConsumeResult {
    Consumed,
    Rejected { index: usize },
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

    /// Atomically record first use of a set of replay keys.
    ///
    /// Production implementations must return `Consumed` only when every
    /// supplied key was consumed together. If any key is already present or
    /// malformed, no key from the set should remain consumed.
    fn consume_nonces(&mut self, nonces: &[String]) -> ReplayConsumeResult;
}

#[derive(Clone, Debug)]
pub struct FileReplayCache {
    store_dir: PathBuf,
}

impl FileReplayCache {
    pub fn new<P: AsRef<Path>>(store_dir: P) -> std::io::Result<Self> {
        let store_dir = store_dir.as_ref().to_path_buf();
        let missing_dirs = Self::missing_directory_chain(&store_dir);
        fs::create_dir_all(&store_dir)?;
        Self::sync_created_directory_chain(&missing_dirs)?;
        File::open(&store_dir)?.sync_all()?;
        Ok(Self { store_dir })
    }

    pub fn store_dir(&self) -> &Path {
        &self.store_dir
    }

    fn nonce_path(&self, nonce: &str) -> PathBuf {
        let digest = Sha256::digest(nonce.as_bytes());
        self.store_dir.join(hex::encode(digest))
    }

    fn missing_directory_chain(store_dir: &Path) -> Vec<PathBuf> {
        let mut missing = Vec::new();
        let mut current = Some(store_dir);
        while let Some(path) = current {
            if path.exists() {
                break;
            }
            missing.push(path.to_path_buf());
            current = path.parent();
        }
        missing
    }

    fn sync_created_directory_chain(missing_dirs: &[PathBuf]) -> io::Result<()> {
        for dir in missing_dirs.iter().rev() {
            File::open(Self::directory_parent_to_sync(dir))?.sync_all()?;
            File::open(dir)?.sync_all()?;
        }
        Ok(())
    }

    fn directory_parent_to_sync(dir: &Path) -> &Path {
        match dir.parent() {
            Some(parent) if !parent.as_os_str().is_empty() => parent,
            _ => Path::new("."),
        }
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

    fn commit_nonce_set(&self, nonces: &[String]) -> io::Result<ReplayConsumeResult> {
        let mut seen = HashSet::new();
        for (index, nonce) in nonces.iter().enumerate() {
            if !valid_nonce_text(nonce) || !seen.insert(nonce.as_str()) {
                return Ok(ReplayConsumeResult::Rejected { index });
            }
        }

        let mut markers: Vec<(PathBuf, File, String)> = Vec::new();
        for (index, nonce) in nonces.iter().enumerate() {
            let path = self.nonce_path(nonce);
            let file = match OpenOptions::new().create_new(true).write(true).open(&path) {
                Ok(file) => file,
                Err(error) if error.kind() == ErrorKind::AlreadyExists => {
                    Self::remove_markers(&markers);
                    return Ok(ReplayConsumeResult::Rejected { index });
                }
                Err(error) => {
                    Self::remove_markers(&markers);
                    return Err(error);
                }
            };
            markers.push((path, file, nonce.clone()));
        }

        for marker_index in 0..markers.len() {
            let write_result = {
                let (_, file, nonce) = &mut markers[marker_index];
                Self::write_and_sync_marker_file(file, nonce)
            };
            if let Err(error) = write_result {
                Self::remove_markers(&markers);
                return Err(error);
            }
        }
        if let Err(error) = File::open(&self.store_dir)?.sync_all() {
            Self::remove_markers(&markers);
            return Err(error);
        }
        Ok(ReplayConsumeResult::Consumed)
    }

    fn remove_markers(markers: &[(PathBuf, File, String)]) {
        for (path, _, _) in markers {
            let _ = fs::remove_file(path);
        }
    }

    fn write_and_sync_marker(file: &mut File, store_dir: &Path, nonce: &str) -> io::Result<()> {
        Self::write_and_sync_marker_file(file, nonce)?;
        File::open(store_dir)?.sync_all()?;
        Ok(())
    }

    fn write_and_sync_marker_file(file: &mut File, nonce: &str) -> io::Result<()> {
        file.write_all(nonce.as_bytes())?;
        file.write_all(b"\n")?;
        file.sync_all()?;
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
        if !valid_nonce_text(nonce) {
            return false;
        }
        self.commit_nonce(nonce).unwrap_or(false)
    }

    fn consume_nonces(&mut self, nonces: &[String]) -> ReplayConsumeResult {
        self.commit_nonce_set(nonces)
            .unwrap_or(ReplayConsumeResult::Rejected { index: 0 })
    }
}

fn valid_nonce_text(nonce: &str) -> bool {
    !nonce.trim().is_empty() && !nonce.contains('\n') && !nonce.contains('\r')
}

#[cfg(test)]
mod tests {
    use super::FileReplayCache;
    use std::path::Path;

    #[test]
    fn first_level_relative_store_syncs_current_directory_parent() {
        assert_eq!(
            FileReplayCache::directory_parent_to_sync(Path::new("store")),
            Path::new(".")
        );
    }

    #[test]
    fn nested_relative_store_syncs_named_parent() {
        assert_eq!(
            FileReplayCache::directory_parent_to_sync(Path::new("nested/store")),
            Path::new("nested")
        );
    }
}
