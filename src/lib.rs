use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::io::Write;

#[cfg(target_os = "linux")]
use std::os::unix::net::UnixDatagram;

#[cfg(target_os = "linux")]
const JOURNALD_PATH: &str = "/run/systemd/journal/socket";

/// Send a message to journald.
///
/// Args:
///     message: The log message (MESSAGE field)
///     message_id: Optional message ID (MESSAGE_ID field)
///     code_file: Optional source file (CODE_FILE field)
///     code_line: Optional source line (CODE_LINE field)
///     code_func: Optional function name (CODE_FUNC field)
///     **kwargs: Additional fields to include in the journal entry
///
/// Example:
///     >>> journald_send.send("Hello World", PRIORITY=6, MY_FIELD="custom")
#[cfg(target_os = "linux")]
#[pyfunction]
#[pyo3(signature = (message, message_id=None, code_file=None, code_line=None, code_func=None, **kwargs))]
fn send(
    py: Python<'_>,
    message: String,
    message_id: Option<String>,
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
        send_to_journald_raw(
            &message,
            message_id.as_deref(),
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
#[pyo3(signature = (message, message_id=None, code_file=None, code_line=None, code_func=None, **kwargs))]
fn send(
    _py: Python<'_>,
    _message: String,
    _message_id: Option<String>,
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
fn send_to_journald_raw(
    message: &str,
    message_id: Option<&str>,
    code_file: Option<&str>,
    code_line: Option<u64>,
    code_func: Option<&str>,
    extra_fields: &[(String, String)],
) -> std::io::Result<()> {
    let socket = UnixDatagram::unbound()?;

    let mut buf = Vec::with_capacity(512);

    // Add MESSAGE field (safe - message doesn't contain newlines)
    put_field_wellformed(&mut buf, "MESSAGE", message.as_bytes());

    // Add optional standard fields
    if let Some(mid) = message_id {
        // Safe - message IDs don't contain newlines
        put_field_wellformed(&mut buf, "MESSAGE_ID", mid.as_bytes());
    }

    if let Some(file) = code_file {
        // Safe - file paths don't contain newlines
        put_field_wellformed(&mut buf, "CODE_FILE", file.as_bytes());
    }

    if let Some(line) = code_line {
        // Safe - line numbers don't contain newlines
        put_field_wellformed(&mut buf, "CODE_LINE", line.to_string().as_bytes());
    }

    if let Some(func) = code_func {
        // Safe - function names don't contain newlines
        put_field_wellformed(&mut buf, "CODE_FUNC", func.as_bytes());
    }

    // Add custom fields
    for (key, value) in extra_fields {
        put_field_length_encoded(&mut buf, &key.to_uppercase(), |buf| {
            buf.extend_from_slice(value.as_bytes());
        });
    }

    // Send the payload
    socket.send_to(&buf, JOURNALD_PATH).or_else(|error| {
        if Some(libc::EMSGSIZE) == error.raw_os_error() {
            send_large_payload(&socket, &buf)
        } else {
            Err(error)
        }
    })?;

    Ok(())
}

#[cfg(target_os = "linux")]
fn send_large_payload(socket: &UnixDatagram, payload: &[u8]) -> std::io::Result<usize> {
    use std::os::unix::prelude::AsRawFd;

    // Create a temporary memfd module inline for large payload support
    mod memfd {
        use std::fs::File;
        use std::io;
        use std::os::unix::io::{AsRawFd, FromRawFd, RawFd};

        pub struct MemFd(File);

        pub fn create_sealable() -> io::Result<MemFd> {
            let name = std::ffi::CString::new("journald-send").unwrap();
            let fd = unsafe { libc::memfd_create(name.as_ptr(), 0) };
            if fd < 0 {
                return Err(io::Error::last_os_error());
            }
            Ok(MemFd(unsafe { File::from_raw_fd(fd) }))
        }

        pub fn seal_fully(fd: RawFd) -> io::Result<()> {
            let seals =
                libc::F_SEAL_SHRINK | libc::F_SEAL_GROW | libc::F_SEAL_WRITE | libc::F_SEAL_SEAL;
            let ret = unsafe { libc::fcntl(fd, libc::F_ADD_SEALS, seals) };
            if ret < 0 {
                return Err(io::Error::last_os_error());
            }
            Ok(())
        }

        impl AsRawFd for MemFd {
            fn as_raw_fd(&self) -> RawFd {
                self.0.as_raw_fd()
            }
        }

        impl std::io::Write for MemFd {
            fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
                self.0.write(buf)
            }

            fn flush(&mut self) -> std::io::Result<()> {
                self.0.flush()
            }
        }
    }

    mod socket {
        use std::io;
        use std::os::unix::net::UnixDatagram;
        use std::os::unix::prelude::AsRawFd;

        pub fn send_one_fd_to(socket: &UnixDatagram, fd: i32, path: &str) -> io::Result<usize> {
            let mut cmsg_space: libc::cmsghdr = unsafe { std::mem::zeroed() };

            let dummy_data: [u8; 1] = [0];
            let mut iov = libc::iovec {
                iov_base: dummy_data.as_ptr() as *mut _,
                iov_len: dummy_data.len(),
            };

            let unix_addr = libc::sockaddr_un {
                sun_family: libc::AF_UNIX as libc::sa_family_t,
                sun_path: {
                    let mut path_buf = [0 as libc::c_char; 108];
                    let path_bytes = path.as_bytes();
                    let copy_len = path_bytes.len().min(107);
                    for (i, &b) in path_bytes[..copy_len].iter().enumerate() {
                        path_buf[i] = b as libc::c_char;
                    }
                    path_buf
                },
            };

            let msg = libc::msghdr {
                msg_name: &unix_addr as *const _ as *mut _,
                msg_namelen: std::mem::size_of::<libc::sockaddr_un>() as libc::socklen_t,
                msg_iov: &mut iov,
                msg_iovlen: 1,
                msg_control: &mut cmsg_space as *mut _ as *mut _,
                msg_controllen: std::mem::size_of::<libc::cmsghdr>(),
                msg_flags: 0,
            };

            let cmsg = unsafe { libc::CMSG_FIRSTHDR(&msg) };
            if cmsg.is_null() {
                return Err(io::Error::new(io::ErrorKind::Other, "CMSG_FIRSTHDR failed"));
            }

            unsafe {
                (*cmsg).cmsg_level = libc::SOL_SOCKET;
                (*cmsg).cmsg_type = libc::SCM_RIGHTS;
                (*cmsg).cmsg_len =
                    libc::CMSG_LEN(std::mem::size_of::<i32>() as u32) as libc::size_t;
                let payload = libc::CMSG_DATA(cmsg) as *mut i32;
                *payload = fd;
            }

            let ret = unsafe { libc::sendmsg(socket.as_raw_fd(), &msg, 0) };
            if ret < 0 {
                return Err(io::Error::last_os_error());
            }
            Ok(ret as usize)
        }
    }

    // Write the whole payload to a memfd
    let mut mem = memfd::create_sealable()?;
    mem.write_all(payload)?;
    // Fully seal the memfd to signal journald that its backing data won't resize anymore
    memfd::seal_fully(mem.as_raw_fd())?;
    socket::send_one_fd_to(socket, mem.as_raw_fd(), JOURNALD_PATH)
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
}
