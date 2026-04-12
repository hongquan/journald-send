use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::io::{self, Write};

#[cfg(target_os = "linux")]
use memfd;
#[cfg(target_os = "linux")]
use rustix::fd::{AsFd, BorrowedFd};
#[cfg(target_os = "linux")]
use rustix::io::IoSlice;
#[cfg(target_os = "linux")]
use rustix::net::{sendmsg_addr, SendAncillaryBuffer, SendAncillaryMessage, SendFlags};
#[cfg(target_os = "linux")]
use rustix::net;
#[cfg(target_os = "linux")]
use std::mem::MaybeUninit;

#[cfg(target_os = "linux")]
const JOURNALD_PATH: &str = "/run/systemd/journal/socket";

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
///     >>> journald_send.send("Hello World", priority=6, MY_FIELD="custom")


// Export named constants for priorities so they are available from Python as
// module-level constants (e.g., _core.PRIORITY_EMERGENCY). The Python wrapper
// package (`src/journald_send/__init__.py`) can re-export nicer names.
#[allow(dead_code)]
pub const PRIORITY_EMERGENCY: u8 = 0;
#[allow(dead_code)]
pub const PRIORITY_ALERT: u8 = 1;
#[allow(dead_code)]
pub const PRIORITY_CRITICAL: u8 = 2;
#[allow(dead_code)]
pub const PRIORITY_ERROR: u8 = 3;
#[allow(dead_code)]
pub const PRIORITY_WARNING: u8 = 4;
#[allow(dead_code)]
pub const PRIORITY_NOTICE: u8 = 5;
#[allow(dead_code)]
pub const PRIORITY_INFO: u8 = 6;
#[allow(dead_code)]
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
        send_to_journald(
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



#[cfg(target_os = "linux")]
fn send_to_journald(
    message: &str,
    priority: Option<u8>,
    code_file: Option<&str>,
    code_line: Option<u64>,
    code_func: Option<&str>,
    extra_fields: &[(String, String)],
) -> io::Result<()> {
    // --- Extract main fields from extra_fields for fallback when explicit params are None ---
    let mut extra_priority: Option<u8> = None;
    let mut extra_code_file: Option<String> = None;
    let mut extra_code_line: Option<u64> = None;
    let mut extra_code_func: Option<String> = None;

    let filtered_extra_fields: Vec<(String, String)> = extra_fields
        .iter()
        .filter_map(|(key, value)| {
            match key.to_uppercase().as_str() {
                "PRIORITY" => {
                    if let Ok(p) = value.parse::<u8>() {
                        extra_priority = Some(p);
                    }
                    None
                }
                "CODE_FILE" => {
                    extra_code_file = Some(value.clone());
                    None
                }
                "CODE_LINE" => {
                    if let Ok(l) = value.parse::<u64>() {
                        extra_code_line = Some(l);
                    }
                    None
                }
                "CODE_FUNC" => {
                    extra_code_func = Some(value.clone());
                    None
                }
                _ => Some((key.clone(), value.clone())),
            }
        })
        .collect();

    // Explicit parameters take precedence; fall back to extra_fields when None.
    let final_priority = priority.or(extra_priority);
    let final_code_file = code_file.or(extra_code_file.as_deref());
    let final_code_line = code_line.or(extra_code_line);
    let final_code_func = code_func.or(extra_code_func.as_deref());

    let addr = net::SocketAddrUnix::new(JOURNALD_PATH)?;
    let socket = net::socket(net::AddressFamily::UNIX, net::SocketType::DGRAM, None)?;
    let mut buf = Vec::with_capacity(512);

    // Add MESSAGE field (safe - message doesn't contain newlines)
    put_field_wellformed(&mut buf, "MESSAGE", message.as_bytes());

    // Add optional standard fields
    if let Some(file) = final_code_file {
        put_field_wellformed(&mut buf, "CODE_FILE", file.as_bytes());
    }

    if let Some(line) = final_code_line {
        put_field_wellformed(&mut buf, "CODE_LINE", line.to_string().as_bytes());
    }

    if let Some(func) = final_code_func {
        put_field_wellformed(&mut buf, "CODE_FUNC", func.as_bytes());
    }

    // Add priority if provided
    if let Some(p) = final_priority {
        put_field_wellformed(&mut buf, "PRIORITY", p.to_string().as_bytes());
    }

    // Add remaining custom fields
    for (key, value) in &filtered_extra_fields {
        put_field_length_encoded(&mut buf, key, |buf| {
            buf.extend_from_slice(value.as_bytes());
        });
    }

    // Send the payload
    match net::sendto(&socket, &buf, net::SendFlags::empty(), &addr) {
        Ok(_n) => Ok(()),
        Err(rustix::io::Errno::MSGSIZE) => {
            send_large_payload(socket.as_fd(), &addr, &buf)
        }
        Err(e) => Err(io::Error::from(e)),
    }
}

#[cfg(target_os = "linux")]
fn send_large_payload(
    socket: BorrowedFd<'_>,
    addr: &net::SocketAddrUnix,
    payload: &[u8],
) -> io::Result<()> {
    // Create a sealable memfd
    let opts = memfd::MemfdOptions::default().allow_sealing(true);
    let mfd = opts.create("journald-send").map_err(|e| io::Error::other(format!("memfd: {}", e)))?;

    // Write payload to memfd
    mfd.as_file().write_all(payload)?;

    // Seal the memfd to prevent further modifications
    mfd.add_seals(&[memfd::FileSeal::SealShrink, memfd::FileSeal::SealGrow])
        .map_err(|e| io::Error::other(format!("memfd seal: {}", e)))?;

    // Send the file descriptor
    send_fd(socket, addr, &mfd)
}

#[cfg(target_os = "linux")]
fn send_fd(socket: BorrowedFd<'_>, addr: &net::SocketAddrUnix, mfd: &memfd::Memfd) -> io::Result<()> {
    let dummy = [0u8; 1];
    let iov = IoSlice::new(&dummy);

    let msg = SendAncillaryMessage::ScmRights(&[mfd.as_file().as_fd()]);
    let mut space = [MaybeUninit::uninit(); rustix::cmsg_space!(ScmRights(1))];
    let mut cmsg_buffer = SendAncillaryBuffer::new(space.as_mut_slice());
    if !cmsg_buffer.push(msg) {
        return Err(io::Error::other("failed to push cmsg"));
    }

    sendmsg_addr(socket, addr, &[iov], &mut cmsg_buffer, SendFlags::empty()).map_err(io::Error::from)?;

    Ok(())
}

/// Mangle a name into journald-compliant form.
fn sanitize_name(name: &str, buf: &mut Vec<u8>) {
    // Copied from tracing-jounrald.
    buf.extend(
        name.bytes()
            .map(|c| if c == b'.' { b'_' } else { c })
            .skip_while(|&c| c == b'_')
            .filter(|&c| c == b'_' || char::from(c).is_ascii_alphanumeric())
            .map(|c| char::from(c).to_ascii_uppercase() as u8),
    );
}

/// Append a sanitized and length-encoded field into `buf`.
///
/// Unlike `put_field_wellformed` this function handles arbitrary field names and values.
///
/// `name` denotes the field name. It gets sanitized before being appended to `buf`.
///
/// `write_value` is invoked with `buf` as argument to append the value data to `buf`.  It must
/// not delete from `buf`, but may append arbitrary data.  This function then determines the length
/// of the data written and adds it in the appropriate place in `buf`.
fn put_field_length_encoded(buf: &mut Vec<u8>, name: &str, write_value: impl FnOnce(&mut Vec<u8>)) {
    // Copied from tracing-jounrald.
    sanitize_name(name, buf);
    buf.push(b'\n');
    buf.extend_from_slice(&[0; 8]); // Length tag, to be populated
    let start = buf.len();
    write_value(buf);
    let end = buf.len();
    buf[start - 8..start].copy_from_slice(&((end - start) as u64).to_le_bytes());
    buf.push(b'\n');
}

/// Append arbitrary data with a well-formed name and value.
///
/// `value` must not contain an internal newline, because this function writes
/// `value` in the new-line separated format.
///
/// For a "newline-safe" variant, see `put_field_length_encoded`.
fn put_field_wellformed(buf: &mut Vec<u8>, name: &str, value: &[u8]) {
    buf.extend_from_slice(name.as_bytes());
    buf.push(b'\n');
    put_value(buf, value);
}

/// Write the value portion of a key-value pair, in newline separated format.
///
/// `value` must not contain an internal newline.
///
/// For a "newline-safe" variant, see `put_field_length_encoded`.
fn put_value(buf: &mut Vec<u8>, value: &[u8]) {
    buf.extend_from_slice(&(value.len() as u64).to_le_bytes());
    buf.extend_from_slice(value);
    buf.push(b'\n');
}

/// A Python module implemented in Rust.

#[pyo3::pymodule]
mod _core {
    #[pymodule_export]
    use super::send;

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
}
