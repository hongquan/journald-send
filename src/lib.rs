use pyo3::prelude::*;
use pyo3::types::PyDict;

#[cfg(target_os = "linux")]
mod linux;

/// Send a message to journald.
///
/// Args:
///     message: The log message (MESSAGE field)
///     code_file: Optional source file (CODE_FILE field)
///     code_line: Optional source line (CODE_LINE field)
///     code_func: Optional function name (CODE_FUNC field)
///     **kwargs: Additional fields to include in the journal entry
///
/// Example:
///     >>> journald_send.send('Hello World', priority=6, MY_FIELD='custom')
// Export named constants for priorities so they are available from Python as
// module-level constants (e.g., _core.PRIORITY_EMERGENCY). The Python wrapper
// package (`src/journald_send/__init__.py`) can re-export nicer names.
pub const PRIORITY_EMERGENCY: u8 = 0;
pub const PRIORITY_ALERT: u8 = 1;
pub const PRIORITY_CRITICAL: u8 = 2;
pub const PRIORITY_ERROR: u8 = 3;
pub const PRIORITY_WARNING: u8 = 4;
pub const PRIORITY_NOTICE: u8 = 5;
pub const PRIORITY_INFO: u8 = 6;
pub const PRIORITY_DEBUG: u8 = 7;

#[cfg(target_os = "linux")]
#[pyfunction]
#[pyo3(signature = (message, priority=None, code_file=None, code_line=None, code_func=None, **kwargs))]
fn send(
    py: Python<'_>,
    message: String,
    priority: Option<u8>,
    code_file: Option<String>,
    code_line: Option<u64>,
    code_func: Option<String>,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<()> {
    // Extract kwargs data before releasing GIL
    let extra_fields: Vec<(String, String)> = if let Some(kw) = kwargs {
        kw.iter()
            .map(|(k, v)| (k.to_string(), v.to_string()))
            .collect()
    } else {
        Vec::new()
    };

    py.detach(|| {
        linux::send_to_journald(
            &message,
            priority,
            code_file.as_deref(),
            code_line,
            code_func.as_deref(),
            &extra_fields,
        )
        .map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to send to journald: {}",
                e
            ))
        })
    })
}

#[cfg(not(target_os = "linux"))]
#[pyfunction]
#[pyo3(signature = (message, priority=None, code_file=None, code_line=None, code_func=None, **kwargs))]
fn send(
    _py: Python<'_>,
    _message: String,
    _priority: Option<u8>,
    _code_file: Option<String>,
    _code_line: Option<u64>,
    _code_func: Option<String>,
    _kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<()> {
    Err(pyo3::exceptions::PyOSError::new_err(
        "journald-send is only supported on Linux",
    ))
}

// This function will normalize the keys before sending to the
// `send_compliant_to_journald` function.
#[cfg(target_os = "linux")]
#[pyfunction]
#[pyo3(signature = (message, entries))]
pub fn send_compliant(
    py: Python<'_>,
    message: String,
    entries: Vec<(String, Vec<u8>)>,
) -> PyResult<()> {
    py.detach(|| {
        // Normalize keys and filter out MESSAGE
        let normalized: Vec<(String, Vec<u8>)> = entries
            .into_iter()
            .filter(|(key, _)| {
                let mut buf = Vec::new();
                linux::sanitize_name(key, &mut buf);
                let sanitized_key = String::from_utf8(buf).unwrap_or_else(|_| key.to_uppercase());
                sanitized_key != "MESSAGE"
            })
            .map(|(key, value)| {
                let mut buf = Vec::new();
                linux::sanitize_name(&key, &mut buf);
                let sanitized_key = String::from_utf8(buf).unwrap_or_else(|_| key.to_uppercase());
                (sanitized_key, value)
            })
            .collect();
        linux::send_compliant_to_journald(&message, &normalized).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to send to journald: {}",
                e
            ))
        })
    })
}

#[cfg(not(target_os = "linux"))]
#[pyfunction]
#[pyo3(signature = (message, entries))]
pub fn send_compliant(_message: String, _entries: Vec<(String, Vec<u8>)>) -> PyResult<()> {
    Err(pyo3::exceptions::PyOSError::new_err(
        "journald-send is only supported on Linux",
    ))
}

/// A Python module implemented in Rust.

#[pyo3::pymodule]
mod _core {
    #[pymodule_export]
    use super::send;
    #[pymodule_export]
    use super::send_compliant;

    // Export underscore-prefixed constants so they are available as module attributes
    #[pymodule_export]
    const _PRI_EMERGENCY: u8 = super::PRIORITY_EMERGENCY;
    #[pymodule_export]
    const _PRI_ALERT: u8 = super::PRIORITY_ALERT;
    #[pymodule_export]
    const _PRI_CRITICAL: u8 = super::PRIORITY_CRITICAL;
    #[pymodule_export]
    const _PRI_ERROR: u8 = super::PRIORITY_ERROR;
    #[pymodule_export]
    const _PRI_WARNING: u8 = super::PRIORITY_WARNING;
    #[pymodule_export]
    const _PRI_NOTICE: u8 = super::PRIORITY_NOTICE;
    #[pymodule_export]
    const _PRI_INFO: u8 = super::PRIORITY_INFO;
    #[pymodule_export]
    const _PRI_DEBUG: u8 = super::PRIORITY_DEBUG;

    #[pymodule_export]
    const _VERSION: &str = env!("CARGO_PKG_VERSION");
}
