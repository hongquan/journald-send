use std::io::{self, Write};

use rustix::fd::{AsFd, BorrowedFd};
use rustix::io::Errno;
use rustix::io::IoSlice;
use rustix::net;
use rustix::net::{SendAncillaryBuffer, SendAncillaryMessage, SendFlags, sendmsg_addr};
use std::mem::MaybeUninit;

const JOURNALD_PATH: &str = "/run/systemd/journal/socket";

pub fn send_to_journald(
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
        .filter_map(|(key, value)| match key.to_uppercase().as_str() {
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
        Ok(n) => {
            // Successfully sent via datagram
            let _ = n; // Ignore bytes sent
            Ok(())
        }
        Err(Errno::MSGSIZE) => {
            // Payload too large for socket buffer, use memfd-based transmission
            send_large_payload(socket.as_fd(), &addr, &buf)
        }
        Err(e) => Err(io::Error::from(e)),
    }
}

fn send_large_payload(
    socket: BorrowedFd<'_>,
    addr: &net::SocketAddrUnix,
    payload: &[u8],
) -> io::Result<()> {
    // Create a sealable memfd
    let opts = memfd::MemfdOptions::default().allow_sealing(true);
    let mfd = opts
        .create("journald-send")
        .map_err(|e| io::Error::other(format!("memfd: {}", e)))?;

    // Write payload to memfd
    mfd.as_file().write_all(payload)?;

    // Seal the memfd to prevent further modifications (per journald protocol)
    // Fully seal: prevent shrink, grow, write, and further sealing
    mfd.add_seals(&[
        memfd::FileSeal::SealShrink,
        memfd::FileSeal::SealGrow,
        memfd::FileSeal::SealWrite,
        memfd::FileSeal::SealSeal,
    ])
    .map_err(|e| io::Error::other(format!("memfd seal: {}", e)))?;

    // Send empty datagram with file descriptor in ancillary message
    let iov = IoSlice::new(&[]);

    let msg = SendAncillaryMessage::ScmRights(&[mfd.as_file().as_fd()]);
    let mut space = [MaybeUninit::uninit(); rustix::cmsg_space!(ScmRights(1))];
    let mut cmsg_buffer = SendAncillaryBuffer::new(space.as_mut_slice());
    if !cmsg_buffer.push(msg) {
        return Err(io::Error::other("failed to push cmsg"));
    }

    sendmsg_addr(socket, addr, &[iov], &mut cmsg_buffer, SendFlags::empty())
        .map_err(io::Error::from)
        .map(|_| ())
}

/// Mangle a name into journald-compliant form.
pub fn sanitize_name(name: &str, buf: &mut Vec<u8>) {
    // Copied from tracing-journald.
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
    // Copied from tracing-journald.
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

// This function will join each entry with `=` before sending to journald.
// The keys must be uppercase, it will strip non-compliant entries.
pub fn send_compliant_to_journald(message: &str, entries: &[(String, Vec<u8>)]) -> io::Result<()> {
    let addr = net::SocketAddrUnix::new(JOURNALD_PATH)?;
    let socket = net::socket(net::AddressFamily::UNIX, net::SocketType::DGRAM, None)?;
    let mut buf = Vec::with_capacity(512);

    // MESSAGE field is always added first
    // Use length-encoded format if message contains newline
    put_entry(&mut buf, "MESSAGE", message.as_bytes());

    for (key, value) in entries {
        // Validate that the key is uppercase, skip non-compliant entries
        if !key
            .chars()
            .all(|c| c.is_ascii_uppercase() || c == b'_' as char)
        {
            continue;
        }

        put_entry(&mut buf, key, value);
    }

    // If no valid entries remain, don't send anything
    if buf.is_empty() {
        return Ok(());
    }

    // Send the payload
    match net::sendto(&socket, &buf, net::SendFlags::empty(), &addr) {
        Ok(n) => {
            let _ = n;
            Ok(())
        }
        Err(Errno::MSGSIZE) => send_large_payload(socket.as_fd(), &addr, &buf),
        Err(e) => Err(io::Error::from(e)),
    }
}

/// Write a key-value entry to `buf` following the journald native protocol.
///
/// Use `KEY=VALUE\n` format if `value` doesn't contain newline,
/// otherwise use `KEY\n<LENGTH>\nVALUE\n` format.
fn put_entry(buf: &mut Vec<u8>, key: &str, value: &[u8]) {
    if value.contains(&b'\n') {
        // Length-encoded format: KEY\n<LENGTH>\nVALUE\n
        buf.extend_from_slice(key.as_bytes());
        buf.push(b'\n');
        buf.extend_from_slice(&(value.len() as u64).to_le_bytes());
        buf.extend_from_slice(value);
        buf.push(b'\n');
    } else {
        // Simple format: KEY=VALUE\n
        buf.extend_from_slice(key.as_bytes());
        buf.push(b'=');
        buf.extend_from_slice(value);
        buf.push(b'\n');
    }
}
