#!/usr/bin/env python3
"""Read-only verifier for the GOV-01 static toolchain acquisition.

This verifier is intentionally narrower than npm.  It accepts only the exact
Darwin/arm64 package-lock closure used by the GOV-01 acquisition envelope,
reads content-addressed npm cache blobs, parses a strict USTAR subset, and
derives the expected node_modules tree without executing package code.

It never writes files, invokes subprocesses, imports networking modules, or
reads npm cache indexes.  Absolute private locators are never printed.
"""

from __future__ import print_function

import argparse
import base64
import ctypes
import errno
import hashlib
import json
import os
import posixpath
import stat
import sys
import unicodedata
import zlib


PROFILE_VERSION = "gov-01-toolchain-static-verifier-v2"
FINGERPRINT_TREE_FD_ABI = "returns-layout-and-volatile-xattr-count-v2"
CONTENT_DOMAIN = b"CLS/GOV01-OFFLINE-CACHE/v1\0"
MEMBER_DOMAIN = b"CLS/GOV01/USTAR-PACKAGE-MEMBERS/v2\0"
CLOSURE_DOMAIN = b"CLS/GOV01/USTAR-CLOSURE/v2\0"
RESOLUTION_DOMAIN = b"CLS/GOV01/NODE-RESOLUTION-CLOSURE/v2\0"
TREE_DOMAIN = b"CLS/GOV01/DETERMINISTIC-NODE-MODULES/v2\0"
MAX_COMPRESSED_TOTAL = 14_000_000
MAX_TAR_STREAM = 24_000_000
MAX_FILE_SIZE = 15_000_000
MAX_MEMBER_COUNT = 5_000
MAX_FINAL_PATH_BYTES = 128
EXPECTED_PLATFORM = "darwin"
EXPECTED_ARCH = "arm64"
ALLOWED_VOLATILE_XATTRS = frozenset(["com.apple.provenance"])
O_SYMLINK_DARWIN = 0x00200000
_FLISTXATTR = None
_ACL_FUNCTIONS = None


class VerificationError(Exception):
    def __init__(self, code, reason):
        Exception.__init__(self, reason)
        self.code = code
        self.reason = reason


def fail(code, reason):
    raise VerificationError(code, reason)


def reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail(11, "duplicate-json-key")
        result[key] = value
    return result


def reject_float(_value):
    fail(11, "json-float-prohibited")


def load_json_bytes(raw, label, strict_text_profile=True):
    if raw.startswith(b"\xef\xbb\xbf") or (strict_text_profile and b"\r" in raw):
        fail(11, label + "-encoding-profile")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail(11, label + "-utf8")
    if unicodedata.normalize("NFC", text) != text:
        fail(11, label + "-non-nfc")
    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicate_pairs,
            parse_float=reject_float,
            parse_constant=lambda _x: fail(11, "json-constant-prohibited"),
        )
    except VerificationError:
        raise
    except Exception:
        fail(11, label + "-invalid-json")


def stable_metadata(info):
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_uid,
        info.st_gid,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        getattr(info, "st_flags", 0),
    )


def read_regular(path, label):
    try:
        info = os.lstat(path)
    except OSError:
        fail(20, label + "-missing")
    if not stat.S_ISREG(info.st_mode):
        fail(20, label + "-not-regular")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode):
                fail(20, label + "-open-not-regular")
            if stable_metadata(info) != stable_metadata(opened):
                fail(20, label + "-open-race")
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            final = os.fstat(fd)
            if stable_metadata(opened) != stable_metadata(final):
                fail(20, label + "-read-race")
        finally:
            os.close(fd)
        try:
            post = os.lstat(path)
        except OSError:
            fail(20, label + "-post-read-missing")
        if stable_metadata(info) != stable_metadata(post):
            fail(20, label + "-post-read-race")
        return b"".join(chunks)
    except VerificationError:
        raise
    except OSError:
        fail(20, label + "-read-failed")


def read_regular_beneath(root_fd, components, label, byte_ceiling):
    """Read one regular file through a stable, no-follow dir-fd chain."""
    if not hasattr(os, "O_NOFOLLOW") or not components or byte_ceiling < 0:
        fail(20, label + "-safe-open-unavailable")
    for component in components:
        if not isinstance(component, str) or component in ("", ".", "..") or "/" in component or "\0" in component:
            fail(20, label + "-bad-component")
    held = []
    try:
        current_fd = os.dup(root_fd)
        root_info = os.fstat(current_fd)
        if not stat.S_ISDIR(root_info.st_mode):
            fail(20, label + "-root-not-directory")
        held.append((current_fd, root_info))
        for component in components[:-1]:
            before = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
                fail(20, label + "-unsafe-ancestor")
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            child_fd = os.open(component, flags, dir_fd=current_fd)
            opened = os.fstat(child_fd)
            if stable_metadata(before) != stable_metadata(opened):
                os.close(child_fd)
                fail(20, label + "-ancestor-open-race")
            post_open = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if stable_metadata(before) != stable_metadata(post_open):
                os.close(child_fd)
                fail(20, label + "-ancestor-entry-race")
            held.append((child_fd, opened))
            current_fd = child_fd

        leaf = components[-1]
        before = os.stat(leaf, dir_fd=current_fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
            fail(20, label + "-not-regular")
        if before.st_nlink != 1:
            fail(20, label + "-hardlink")
        file_fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=current_fd)
        try:
            opened = os.fstat(file_fd)
            if stable_metadata(before) != stable_metadata(opened):
                fail(20, label + "-file-open-race")
            chunks = []
            size = 0
            while True:
                chunk = os.read(file_fd, min(1024 * 1024, byte_ceiling - size + 1))
                if not chunk:
                    break
                size += len(chunk)
                if size > byte_ceiling:
                    fail(23, "compressed-closure-too-large")
                chunks.append(chunk)
            final = os.fstat(file_fd)
            if stable_metadata(opened) != stable_metadata(final):
                fail(20, label + "-file-read-race")
        finally:
            os.close(file_fd)
        post = os.stat(leaf, dir_fd=current_fd, follow_symlinks=False)
        if stable_metadata(before) != stable_metadata(post):
            fail(20, label + "-file-entry-race")
        for directory_fd, baseline in held:
            if stable_metadata(baseline) != stable_metadata(os.fstat(directory_fd)):
                fail(20, label + "-ancestor-metadata-race")
        return b"".join(chunks)
    except VerificationError:
        raise
    except OSError:
        fail(20, label + "-safe-read-failed")
    finally:
        for directory_fd, _baseline in reversed(held):
            try:
                os.close(directory_fd)
            except OSError:
                pass


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def list_xattrs_fd(fd):
    """Return xattr names without reading values (Darwin flistxattr)."""
    if sys.platform != "darwin":
        fail(22, "xattr-verifier-platform")
    global _FLISTXATTR
    if _FLISTXATTR is None:
        libc = ctypes.CDLL(None, use_errno=True)
        function = libc.flistxattr
        function.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
        function.restype = ctypes.c_ssize_t
        _FLISTXATTR = function
    function = _FLISTXATTR
    size = function(fd, None, 0, 0)
    if size < 0:
        fail(50, "xattr-list-size")
    if size == 0:
        return set()
    buffer = ctypes.create_string_buffer(size)
    received = function(fd, ctypes.cast(buffer, ctypes.c_void_p), size, 0)
    if received != size:
        fail(50, "xattr-list-race")
    names = set()
    for item in buffer.raw[:size].split(b"\0"):
        if not item:
            continue
        try:
            decoded = item.decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(50, "xattr-name-encoding")
        names.add(decoded)
    return names


def assert_no_extended_acl_fd(fd):
    """Reject every Darwin extended ACL entry on an already-open object."""
    if sys.platform != "darwin":
        fail(22, "acl-verifier-platform")
    global _ACL_FUNCTIONS
    if _ACL_FUNCTIONS is None:
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            get_fd = libc.acl_get_fd_np
            get_fd.argtypes = [ctypes.c_int, ctypes.c_int]
            get_fd.restype = ctypes.c_void_p
            get_entry = libc.acl_get_entry
            get_entry.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
            get_entry.restype = ctypes.c_int
            free_acl = libc.acl_free
            free_acl.argtypes = [ctypes.c_void_p]
            free_acl.restype = ctypes.c_int
        except (OSError, AttributeError):
            fail(50, "acl-api-unavailable")
        _ACL_FUNCTIONS = (get_fd, get_entry, free_acl)
    get_fd, get_entry, free_acl = _ACL_FUNCTIONS
    ctypes.set_errno(0)
    acl = get_fd(fd, 0x00000100)  # ACL_TYPE_EXTENDED
    if not acl:
        if ctypes.get_errno() == errno.ENOENT:
            return
        fail(50, "acl-get-failed")
    try:
        entry = ctypes.c_void_p()
        ctypes.set_errno(0)
        result = get_entry(acl, 0, ctypes.byref(entry))  # ACL_FIRST_ENTRY
        if result == 0:
            fail(50, "tree-extended-acl")
        if result != -1:
            fail(50, "acl-entry-result")
        if ctypes.get_errno() not in (0, errno.ENOENT):
            fail(50, "acl-entry-failed")
    finally:
        if free_acl(acl) != 0:
            fail(50, "acl-free-failed")


def validate_ascii_field(value, label):
    if not isinstance(value, str) or not value:
        fail(23, label + "-empty")
    if unicodedata.normalize("NFC", value) != value:
        fail(23, label + "-non-nfc")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError:
        fail(23, label + "-non-ascii")
    if any(byte < 0x20 or byte == 0x7F for byte in encoded):
        fail(23, label + "-control")
    if "\t" in value or "\n" in value or "\r" in value:
        fail(23, label + "-tsv-control")
    return value


def allowed_for_host(meta):
    os_values = meta.get("os") or []
    cpu_values = meta.get("cpu") or []
    if not isinstance(os_values, list) or not isinstance(cpu_values, list):
        fail(23, "invalid-os-cpu-selector")

    def allowed(values, selected):
        if not values:
            return True
        if ("!" + selected) in values:
            return False
        positives = [value for value in values if not value.startswith("!")]
        return not positives or selected in positives

    return allowed(os_values, EXPECTED_PLATFORM) and allowed(cpu_values, EXPECTED_ARCH)


def split_sri(integrity):
    if not isinstance(integrity, str) or not integrity.startswith("sha512-"):
        fail(23, "non-sha512-integrity")
    encoded = integrity[len("sha512-") :]
    try:
        digest = base64.b64decode(encoded, validate=True)
    except Exception:
        fail(23, "bad-integrity-base64")
    if len(digest) != 64:
        fail(23, "bad-integrity-length")
    return digest


def cache_blob_path(cache_root, digest):
    hexed = digest.hex()
    return os.path.join(
        cache_root,
        "_cacache",
        "content-v2",
        "sha512",
        hexed[0:2],
        hexed[2:4],
        hexed[4:],
    )


def cache_blob_components(digest):
    hexed = digest.hex()
    return ("_cacache", "content-v2", "sha512", hexed[0:2], hexed[2:4], hexed[4:])


def load_cache_blob_set(cache_root, cache_info, selected):
    if not hasattr(os, "O_NOFOLLOW"):
        fail(20, "cache-safe-open-unavailable")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        cache_fd = os.open(cache_root, flags)
    except OSError:
        fail(20, "cache-root-open-failed")
    try:
        opened = os.fstat(cache_fd)
        if stable_metadata(cache_info) != stable_metadata(opened):
            fail(20, "cache-root-open-race")
        blobs = {}
        total = 0
        for lock_key in sorted(selected, key=lambda value: value.encode("utf-8")):
            meta = selected[lock_key]
            digest = split_sri(meta["integrity"])
            compressed = read_regular_beneath(
                cache_fd,
                cache_blob_components(digest),
                "cache-content",
                MAX_COMPRESSED_TOTAL - total,
            )
            actual_integrity = "sha512-" + base64.b64encode(hashlib.sha512(compressed).digest()).decode("ascii")
            if actual_integrity != meta["integrity"]:
                fail(23, "cache-content-integrity-mismatch")
            total += len(compressed)
            blobs[lock_key] = compressed
        final = os.fstat(cache_fd)
        if stable_metadata(opened) != stable_metadata(final):
            fail(20, "cache-root-read-race")
    finally:
        os.close(cache_fd)
    try:
        post = os.lstat(cache_root)
    except OSError:
        fail(20, "cache-root-post-read-missing")
    if stable_metadata(cache_info) != stable_metadata(post):
        fail(20, "cache-root-post-read-race")
    return blobs


def parse_octal(field, label):
    stripped = field.rstrip(b"\0 ").lstrip(b" ")
    if not stripped:
        return 0
    if any(byte < ord("0") or byte > ord("7") for byte in stripped):
        fail(23, label + "-non-octal")
    try:
        return int(stripped, 8)
    except ValueError:
        fail(23, label + "-bad-octal")


def parse_ustar_text(field, label):
    """Return one strict USTAR text field and reject hidden tail bytes."""
    terminator = field.find(b"\0")
    if terminator < 0:
        return field
    if any(field[terminator + 1 :]):
        fail(23, label + "-nonzero-padding")
    return field[:terminator]


def strict_relpath(path, label):
    validate_ascii_field(path, label)
    if path.startswith("/") or "\\" in path:
        fail(23, label + "-absolute-or-backslash")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        fail(23, label + "-bad-segment")
    if len(path.encode("utf-8")) > MAX_FINAL_PATH_BYTES:
        fail(23, label + "-too-long")
    return path


def inflate_single_gzip(compressed):
    inflater = zlib.decompressobj(16 + zlib.MAX_WBITS)
    try:
        raw = inflater.decompress(compressed, MAX_TAR_STREAM + 1)
    except zlib.error:
        fail(23, "gzip-decompression-failed")
    if len(raw) > MAX_TAR_STREAM:
        fail(23, "tar-stream-too-large")
    # Never call flush while the bounded decompress still has input waiting.
    # That state means the output ceiling, not the compressed input, stopped it.
    if inflater.unconsumed_tail:
        fail(23, "tar-stream-too-large")
    if not inflater.eof or inflater.unused_data:
        fail(23, "gzip-multistream-or-trailing-data")
    remaining = MAX_TAR_STREAM - len(raw)
    try:
        flushed = inflater.flush(remaining + 1)
    except zlib.error:
        fail(23, "gzip-flush-failed")
    if len(flushed) > remaining:
        fail(23, "tar-stream-too-large")
    raw += flushed
    if len(raw) % 512 != 0:
        fail(23, "tar-stream-not-block-aligned")
    return raw


def package_name_from_lock_path(lock_path):
    marker = "node_modules/"
    if not lock_path.startswith(marker):
        fail(23, "lock-path-outside-node-modules")
    tail = lock_path.rsplit(marker, 1)[1]
    strict_relpath(tail, "package-name-from-lock")
    if tail.startswith("@"):
        if len(tail.split("/")) != 2:
            fail(23, "bad-scoped-package-location")
    elif "/" in tail:
        fail(23, "bad-package-location")
    return tail


def add_directory(layout, path):
    if path in layout:
        if layout[path][0] != "D":
            fail(23, "tree-kind-collision")
        return
    layout[path] = ("D", 0o755, 0, "-")


def add_parents(layout, path):
    parent = posixpath.dirname(path)
    pending = []
    while parent and parent != ".":
        pending.append(parent)
        parent = posixpath.dirname(parent)
    for item in reversed(pending):
        add_directory(layout, item)


def parse_package_archive(lock_path, meta, compressed, layout, retain_bytes=False):
    raw = inflate_single_gzip(compressed)
    offset = 0
    member_index = 0
    regular_count = 0
    directory_count = 0
    raw_regular_count = 0
    raw_directory_count = 0
    payload_bytes = 0
    zero_blocks = 0
    roots = set()
    member_rows = []
    package_json_raw = None
    package_files = {} if retain_bytes else None
    seen_output = set()

    while offset < len(raw):
        header = raw[offset : offset + 512]
        offset += 512
        if header == b"\0" * 512:
            zero_blocks += 1
            if zero_blocks < 2:
                continue
            if any(raw[offset:]):
                fail(23, "tar-nonzero-after-eoa")
            offset = len(raw)
            break
        if zero_blocks:
            fail(23, "tar-single-zero-block")
        if header[257:263] != b"ustar\0" or header[263:265] != b"00":
            fail(23, "tar-not-strict-ustar")
        expected_checksum = parse_octal(header[148:156], "tar-checksum")
        checksum_header = header[:148] + (b" " * 8) + header[156:]
        if sum(checksum_header) != expected_checksum:
            fail(23, "tar-checksum-mismatch")
        name_bytes = parse_ustar_text(header[0:100], "tar-name")
        prefix_bytes = parse_ustar_text(header[345:500], "tar-prefix")
        parse_ustar_text(header[157:257], "tar-linkname")
        parse_ustar_text(header[265:297], "tar-uname")
        parse_ustar_text(header[297:329], "tar-gname")
        if any(header[500:512]):
            fail(23, "tar-header-nonzero-padding")
        parse_octal(header[108:116], "tar-uid")
        parse_octal(header[116:124], "tar-gid")
        parse_octal(header[136:148], "tar-mtime")
        parse_octal(header[329:337], "tar-devmajor")
        parse_octal(header[337:345], "tar-devminor")
        typeflag = header[156:157]
        if typeflag not in (b"\0", b"0", b"5"):
            fail(23, "tar-unsupported-type")
        combined = prefix_bytes + (b"/" if prefix_bytes else b"") + name_bytes
        try:
            raw_path = combined.decode("ascii")
        except UnicodeDecodeError:
            fail(23, "tar-path-non-ascii")
        if raw_path.endswith("/"):
            if typeflag != b"5":
                fail(23, "tar-regular-trailing-slash")
            if raw_path.endswith("//"):
                fail(23, "tar-directory-empty-segment")
            raw_path = raw_path[:-1]
        validate_ascii_field(raw_path, "tar-raw-path")
        parts = raw_path.split("/")
        if any(part in ("", ".", "..") for part in parts) or "\\" in raw_path:
            fail(23, "tar-unsafe-path")
        roots.add(parts[0])
        stripped_parts = parts[1:]
        stripped = "/".join(stripped_parts)
        if "node_modules" in stripped_parts:
            fail(23, "tar-bundled-node-modules-prohibited")
        raw_mode = parse_octal(header[100:108], "tar-mode")
        size = parse_octal(header[124:136], "tar-size")
        if size > MAX_FILE_SIZE:
            fail(23, "tar-member-too-large")
        padded = ((size + 511) // 512) * 512
        if offset + padded > len(raw):
            fail(23, "tar-truncated-member")
        payload = raw[offset : offset + size]
        padding = raw[offset + size : offset + padded]
        if any(padding):
            fail(23, "tar-nonzero-member-padding")
        offset += padded
        member_index += 1
        if member_index > MAX_MEMBER_COUNT:
            fail(23, "tar-too-many-members")

        is_dir = typeflag == b"5"
        if is_dir and size != 0:
            fail(23, "tar-directory-with-payload")
        kind = "D" if is_dir else "F"
        if is_dir:
            raw_directory_count += 1
        else:
            raw_regular_count += 1
        digest = "-" if is_dir else sha256_hex(payload)
        if stripped:
            strict_relpath(stripped, "tar-stripped-path")
            base = lock_path[len("node_modules/") :]
            final_path = "node_modules/" + base + "/" + stripped
            strict_relpath(final_path, "tree-path")
            collision_key = unicodedata.normalize("NFC", final_path).casefold()
            if collision_key in seen_output:
                fail(23, "package-output-path-collision")
            seen_output.add(collision_key)
            add_parents(layout, final_path)
            if kind == "D":
                add_directory(layout, final_path)
                directory_count += 1
            else:
                mode = 0o755 if (raw_mode & 0o111) else 0o644
                if final_path in layout:
                    fail(23, "tree-file-collision")
                layout[final_path] = ("F", mode, size, digest)
                regular_count += 1
                payload_bytes += size
                if stripped == "package.json":
                    package_json_raw = payload
                if retain_bytes:
                    package_files[final_path] = payload
        member_rows.append(
            "\t".join(
                [
                    lock_path,
                    str(member_index),
                    kind,
                    raw_path,
                    stripped or "-",
                    format(raw_mode & 0o7777, "04o"),
                    str(size),
                    digest,
                ]
            )
        )

    if zero_blocks < 2 or len(roots) != 1:
        fail(23, "tar-eoa-or-root-count")
    if package_json_raw is None:
        fail(23, "package-json-missing")
    # Registry package.json bytes are immutable SRI-bound payloads, but their
    # original whitespace (including CRLF) is package data rather than a GOV
    # control-artifact encoding profile.
    package_json = load_json_bytes(package_json_raw, "package-json", strict_text_profile=False)
    expected_name = package_name_from_lock_path(lock_path)
    validate_ascii_field(package_json.get("name"), "package-name")
    validate_ascii_field(package_json.get("version"), "package-version")
    if package_json.get("name") != expected_name:
        fail(23, "package-name-mismatch")
    if package_json.get("version") != meta.get("version"):
        fail(23, "package-version-mismatch")
    if package_json.get("bundledDependencies") or package_json.get("bundleDependencies"):
        fail(23, "bundled-dependency-prohibited")

    member_body = ("\n".join(sorted(member_rows)) + "\n").encode("utf-8")
    member_digest = sha256_hex(MEMBER_DOMAIN + member_body)
    scripts = package_json.get("scripts") or {}
    lifecycle_names = set(["preinstall", "install", "postinstall", "prepare"])
    lifecycle_count = len([name for name in scripts if name in lifecycle_names]) if isinstance(scripts, dict) else 0
    return {
        "tar_bytes": len(raw),
        "member_count": member_index,
        "regular_count": regular_count,
        "directory_count": directory_count,
        "raw_regular_count": raw_regular_count,
        "raw_directory_count": raw_directory_count,
        "payload_bytes": payload_bytes,
        "strip_root": next(iter(roots)),
        "package_name": package_json["name"],
        "package_version": package_json["version"],
        "package_json": package_json,
        "member_manifest_sha256": member_digest,
        "lifecycle_count": lifecycle_count,
        "files": package_files,
    }


def normalize_bin(package_name, value):
    if value is None:
        return {}
    if isinstance(value, str):
        value = {package_name.split("/")[-1]: value}
    if not isinstance(value, dict):
        fail(23, "invalid-bin-shape")
    result = {}
    for name, target in value.items():
        validate_ascii_field(name, "bin-name")
        validate_ascii_field(target, "bin-target")
        if target.startswith("/") or "\\" in target:
            fail(23, "bin-target-absolute-or-backslash")
        normalized = posixpath.normpath(target)
        if normalized in ("", ".", "..") or normalized.startswith("../"):
            fail(23, "bin-target-escape")
        strict_relpath(normalized, "bin-target")
        result[name] = normalized
    return result


def add_bin_links(packages, selected, layout):
    link_count = 0
    for lock_path in sorted(selected):
        package = packages[lock_path]
        package_name = package["package_json"]["name"]
        lock_bin = normalize_bin(package_name, selected[lock_path].get("bin"))
        manifest_bin = normalize_bin(package_name, package["package_json"].get("bin"))
        if lock_bin != manifest_bin:
            fail(23, "bin-lock-manifest-mismatch:" + package_name)
        if not lock_bin:
            continue
        # A scoped package lives below node_modules/@scope/name, but its bin
        # links belong to the enclosing node_modules/.bin, not @scope/.bin.
        marker_index = lock_path.rfind("node_modules/")
        if marker_index < 0:
            fail(23, "bin-package-location")
        enclosing_node_modules = lock_path[:marker_index] + "node_modules"
        bin_dir = enclosing_node_modules + "/.bin"
        add_directory(layout, bin_dir)
        for bin_name in sorted(lock_bin):
            target = lock_path + "/" + lock_bin[bin_name]
            link_path = bin_dir + "/" + bin_name
            strict_relpath(link_path, "bin-link-path")
            if target not in layout or layout[target][0] != "F":
                fail(23, "bin-target-not-regular")
            link_text = posixpath.relpath(target, bin_dir)
            if link_path in layout:
                fail(23, "bin-link-collision")
            layout[link_path] = ("L", 0o777, len(link_text.encode("utf-8")), link_text)
            link_count += 1
    return link_count


def resolve_dependency(selected, source, dep_name):
    current = source
    while True:
        if current:
            candidate = current + "/node_modules/" + dep_name
        else:
            candidate = "node_modules/" + dep_name
        if candidate in selected:
            return candidate
        if not current:
            return None
        marked = "/" + current
        index = marked.rfind("/node_modules/")
        if index < 0:
            current = ""
        else:
            current = marked[:index].lstrip("/")


def resolution_manifest(lock, selected, all_packages):
    """Fingerprint lockfile path resolution only; this is not a semver proof."""
    rows = []
    required_missing = 0
    allowed_missing = 0

    def add_edges(source, edge_type, edges, optional_peer_names=None):
        nonlocal required_missing, allowed_missing
        if not edges:
            return
        if not isinstance(edges, dict):
            fail(23, "invalid-dependency-map")
        optional_peer_names = optional_peer_names or set()
        for dep_name in sorted(edges):
            spec = edges[dep_name]
            validate_ascii_field(dep_name, "dependency-name")
            if not isinstance(spec, str):
                fail(23, "dependency-spec-not-string")
            validate_ascii_field(spec, "dependency-spec")
            target = resolve_dependency(selected, source, dep_name)
            state = "resolved"
            target_version = "-"
            target_value = "-"
            if target is not None:
                target_value = target
                target_version = selected[target].get("version") or "-"
            else:
                lock_candidates = [path for path in all_packages if path.endswith("node_modules/" + dep_name)]
                host_blocked = any(not allowed_for_host(all_packages[path]) for path in lock_candidates)
                if edge_type == "optional" and host_blocked:
                    state = "allowed-platform-optional-missing"
                    allowed_missing += 1
                elif edge_type == "peer" and dep_name in optional_peer_names:
                    state = "allowed-optional-peer-missing"
                    allowed_missing += 1
                else:
                    state = "required-missing"
                    required_missing += 1
            rows.append(
                "\t".join(
                    [source or "<root>", edge_type, dep_name, spec, target_value, target_version, state]
                )
            )

    root = lock.get("packages", {}).get("") or {}
    root_optional = root.get("optionalDependencies") or {}
    root_dependencies = dict(root.get("dependencies") or {})
    for name in root_optional:
        root_dependencies.pop(name, None)
    root_peer_meta = root.get("peerDependenciesMeta") or {}
    root_optional_peers = set(
        name for name, value in root_peer_meta.items() if isinstance(value, dict) and value.get("optional") is True
    )
    add_edges("", "root-dependency", root_dependencies)
    add_edges("", "root-dev", root.get("devDependencies"))
    add_edges("", "root-optional", root_optional)
    add_edges("", "root-peer", root.get("peerDependencies"), root_optional_peers)
    for source in sorted(selected):
        meta = selected[source]
        optional = meta.get("optionalDependencies") or {}
        dependencies = dict(meta.get("dependencies") or {})
        for name in optional:
            dependencies.pop(name, None)
        peer_meta = meta.get("peerDependenciesMeta") or {}
        optional_peer_names = set(
            name for name, value in peer_meta.items() if isinstance(value, dict) and value.get("optional") is True
        )
        add_edges(source, "dependency", dependencies)
        add_edges(source, "optional", optional)
        add_edges(source, "peer", meta.get("peerDependencies"), optional_peer_names)
    body = ("\n".join(sorted(rows)) + "\n").encode("utf-8")
    return {
        "row_count": len(rows),
        "body_bytes": len(body),
        "sha256": sha256_hex(RESOLUTION_DOMAIN + body),
        "required_missing": required_missing,
        "allowed_missing": allowed_missing,
    }


def layout_manifest(layout):
    rows = []
    counts = {"F": 0, "D": 0, "L": 0}
    seen_casefold = set()
    for path in sorted(layout, key=lambda value: value.encode("utf-8")):
        strict_relpath(path, "layout-path")
        folded = unicodedata.normalize("NFC", path).casefold()
        if folded in seen_casefold:
            fail(23, "layout-casefold-collision")
        seen_casefold.add(folded)
        kind, mode, size, identity = layout[path]
        counts[kind] += 1
        rows.append("\t".join([kind, path, format(mode, "04o"), str(size), identity]))
    body = ("\n".join(rows) + "\n").encode("utf-8")
    return {
        "entry_count": len(rows),
        "file_count": counts["F"],
        "directory_count": counts["D"],
        "symlink_count": counts["L"],
        "body_bytes": len(body),
        "sha256": sha256_hex(TREE_DOMAIN + body),
    }


def build_expected(repo_root, cache_root, retain_bytes=False):
    if (
        not isinstance(cache_root, str)
        or not os.path.isabs(cache_root)
        or os.path.normpath(cache_root) != cache_root
        or os.path.realpath(cache_root) != cache_root
    ):
        fail(20, "cache-root-invalid")
    try:
        cache_info = os.lstat(cache_root)
    except OSError:
        fail(20, "cache-root-missing")
    if not stat.S_ISDIR(cache_info.st_mode) or stat.S_ISLNK(cache_info.st_mode):
        fail(20, "cache-root-not-real-directory")
    lock_path = os.path.join(repo_root, "package-lock.json")
    package_path = os.path.join(repo_root, "package.json")
    lock_raw = read_regular(lock_path, "package-lock")
    package_raw = read_regular(package_path, "package-manifest")
    lock = load_json_bytes(lock_raw, "package-lock")
    package = load_json_bytes(package_raw, "package-manifest")
    if lock.get("lockfileVersion") != 3:
        fail(23, "lockfile-version")
    validate_ascii_field(package.get("name"), "root-package-name")
    validate_ascii_field(package.get("version"), "root-package-version")
    validate_ascii_field(lock.get("name"), "root-lock-name")
    validate_ascii_field(lock.get("version"), "root-lock-version")
    if lock.get("name") != package.get("name") or lock.get("version") != package.get("version"):
        fail(23, "root-package-lock-identity")
    all_packages = lock.get("packages")
    if not isinstance(all_packages, dict):
        fail(23, "lock-packages-not-object")
    lock_root = all_packages.get("")
    if not isinstance(lock_root, dict):
        fail(23, "lock-root-package-missing")
    for dependency_key in (
        "dependencies",
        "devDependencies",
        "optionalDependencies",
        "peerDependencies",
    ):
        package_has = dependency_key in package
        lock_has = dependency_key in lock_root
        if package_has != lock_has:
            fail(23, "root-dependency-map-presence-mismatch")
        if not package_has:
            continue
        package_dependencies = package.get(dependency_key)
        lock_dependencies = lock_root.get(dependency_key)
        if not isinstance(package_dependencies, dict) or not isinstance(lock_dependencies, dict):
            fail(23, "root-dependency-map-shape")
        for dependency_name, dependency_spec in package_dependencies.items():
            validate_ascii_field(dependency_name, "root-dependency-name")
            if not isinstance(dependency_spec, str):
                fail(23, "root-dependency-spec-shape")
            validate_ascii_field(dependency_spec, "root-dependency-spec")
        if package_dependencies != lock_dependencies:
            fail(23, "root-dependency-map-mismatch")
    selected = {}
    for lock_key, meta in all_packages.items():
        if not lock_key:
            continue
        strict_relpath(lock_key, "lock-package-path")
        if not isinstance(meta, dict):
            fail(23, "lock-package-not-object")
        if meta.get("link") or meta.get("inBundle"):
            fail(23, "link-or-bundle-package-prohibited")
        resolved = meta.get("resolved")
        integrity = meta.get("integrity")
        if not isinstance(resolved, str) or not resolved.startswith("https://registry.npmjs.org/"):
            fail(23, "non-registry-package")
        validate_ascii_field(resolved, "registry-url")
        validate_ascii_field(meta.get("version"), "lock-package-version")
        split_sri(integrity)
        if allowed_for_host(meta):
            selected[lock_key] = meta
    compressed_by_lock = load_cache_blob_set(cache_root, cache_info, selected)
    layout = {"node_modules": ("D", 0o755, 0, "-")}
    package_records = {}
    closure_rows = []
    content_rows = []
    compressed_total = 0
    tar_total = 0
    payload_total = 0
    raw_members = 0
    raw_regular_count = 0
    raw_directory_count = 0
    lifecycle_field_count = 0

    for lock_key in sorted(selected, key=lambda value: value.encode("utf-8")):
        meta = selected[lock_key]
        compressed = compressed_by_lock[lock_key]
        actual_integrity = "sha512-" + base64.b64encode(hashlib.sha512(compressed).digest()).decode("ascii")
        if actual_integrity != meta["integrity"]:
            fail(23, "cache-content-integrity-mismatch")
        compressed_total += len(compressed)
        if compressed_total > MAX_COMPRESSED_TOTAL:
            fail(23, "compressed-closure-too-large")
        record = parse_package_archive(lock_key, meta, compressed, layout, retain_bytes=retain_bytes)
        package_records[lock_key] = record
        tar_total += record["tar_bytes"]
        payload_total += record["payload_bytes"]
        raw_members += record["member_count"]
        raw_regular_count += record["raw_regular_count"]
        raw_directory_count += record["raw_directory_count"]
        lifecycle_field_count += record["lifecycle_count"]
        closure_rows.append(
            "\t".join(
                [
                    lock_key,
                    meta["version"],
                    meta["integrity"],
                    str(len(compressed)),
                    str(record["tar_bytes"]),
                    str(record["member_count"]),
                    str(record["raw_regular_count"]),
                    str(record["raw_directory_count"]),
                    str(record["payload_bytes"]),
                    record["strip_root"],
                    record["package_name"],
                    record["package_version"],
                    record["member_manifest_sha256"],
                ]
            )
        )
        content_rows.append(
            "\t".join(
                [
                    lock_key,
                    meta["version"],
                    meta["resolved"],
                    meta["integrity"],
                    str(len(compressed)),
                    actual_integrity,
                ]
            )
        )

    content_body = ("\n".join(sorted(content_rows)) + "\n").encode("utf-8")
    closure_body = ("\n".join(sorted(closure_rows)) + "\n").encode("utf-8")
    bin_count = add_bin_links(package_records, selected, layout)
    resolution = resolution_manifest(lock, selected, all_packages)
    if resolution["required_missing"] != 0:
        fail(23, "required-dependency-missing")
    tree = layout_manifest(layout)
    return {
        "profile_version": PROFILE_VERSION,
        "package_json_sha256": sha256_hex(package_raw),
        "package_lock_sha256": sha256_hex(lock_raw),
        "lockfile_version": 3,
        "lock_package_count": len(all_packages) - 1,
        "selected_package_count": len(selected),
        "excluded_platform_package_count": (len(all_packages) - 1) - len(selected),
        "compressed_bytes": compressed_total,
        "tar_stream_bytes": tar_total,
        "payload_bytes": payload_total,
        "raw_member_count": raw_members,
        "raw_regular_count": raw_regular_count,
        "raw_directory_count": raw_directory_count,
        "bin_link_count": bin_count,
        "lifecycle_field_count": lifecycle_field_count,
        "content_receipt_body_bytes": len(content_body),
        "content_receipt_sha256": sha256_hex(CONTENT_DOMAIN + content_body),
        "ustar_closure_body_bytes": len(closure_body),
        "ustar_closure_sha256": sha256_hex(CLOSURE_DOMAIN + closure_body),
        "resolution": resolution,
        "tree": tree,
        "layout": layout,
        "package_records": package_records,
        "selected": selected,
    }


def metadata_fingerprint(info):
    return stable_metadata(info)


def fingerprint_tree_fd(root_fd):
    """Return exactly ``(layout, allowed_volatile_xattr_path_count)``."""
    layout = {}
    owner_uid = os.getuid()
    owner_gid = os.getgid()
    volatile_xattr_path_count = 0

    def require_same_metadata(before, after, label):
        if metadata_fingerprint(before) != metadata_fingerprint(after):
            fail(50, label + "-metadata-race")

    def lstat_child(parent_fd, name, label):
        try:
            return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError:
            fail(50, label + "-lstat-failed")

    def scan_names(directory_fd):
        try:
            entries = list(os.scandir(directory_fd))
        except OSError:
            fail(50, "tree-scan-failed")
        names = []
        for entry in entries:
            validate_ascii_field(entry.name, "tree-entry-name")
            names.append(entry.name)
        if len(names) != len(set(names)):
            fail(50, "tree-duplicate-directory-entry")
        return sorted(names, key=lambda value: value.encode("utf-8"))

    def check_metadata(opened_fd, info, count_xattr):
        nonlocal volatile_xattr_path_count
        if getattr(info, "st_flags", 0) != 0:
            fail(50, "tree-file-flags")
        assert_no_extended_acl_fd(opened_fd)
        names = list_xattrs_fd(opened_fd)
        unexpected = names.difference(ALLOWED_VOLATILE_XATTRS)
        if unexpected:
            fail(50, "tree-unapproved-xattr")
        if count_xattr and names:
            volatile_xattr_path_count += 1
        return names

    def walk(fd, path, parent_lstat=None):
        try:
            initial = os.fstat(fd)
        except OSError:
            fail(50, "tree-directory-fstat-failed")
        if parent_lstat is not None:
            require_same_metadata(parent_lstat, initial, "tree-directory-open")
        if not stat.S_ISDIR(initial.st_mode):
            fail(50, "tree-root-not-directory")
        if initial.st_uid != owner_uid or initial.st_gid != owner_gid:
            fail(50, "tree-owner-mismatch")
        initial_xattrs = check_metadata(fd, initial, True)
        layout[path] = ("D", stat.S_IMODE(initial.st_mode), 0, "-")
        names_before = scan_names(fd)
        for name in names_before:
            child_path = path + "/" + name
            strict_relpath(child_path, "actual-tree-path")
            child_info = lstat_child(fd, name, "tree-child")
            mode = stat.S_IMODE(child_info.st_mode)
            if child_info.st_uid != owner_uid or child_info.st_gid != owner_gid:
                fail(50, "tree-owner-mismatch")
            if stat.S_ISDIR(child_info.st_mode):
                flags = os.O_RDONLY | os.O_DIRECTORY
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                try:
                    child_fd = os.open(name, flags, dir_fd=fd)
                except OSError:
                    fail(50, "tree-open-directory-failed")
                try:
                    walk(child_fd, child_path, child_info)
                finally:
                    os.close(child_fd)
                require_same_metadata(child_info, lstat_child(fd, name, "tree-directory-post"), "tree-directory")
            elif stat.S_ISREG(child_info.st_mode):
                if child_info.st_nlink != 1:
                    fail(50, "tree-file-hardlink")
                flags = os.O_RDONLY
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                try:
                    child_fd = os.open(name, flags, dir_fd=fd)
                except OSError:
                    fail(50, "tree-open-file-failed")
                try:
                    opened_info = os.fstat(child_fd)
                    require_same_metadata(child_info, opened_info, "tree-file-open")
                    initial_file_xattrs = check_metadata(child_fd, opened_info, True)
                    digest = hashlib.sha256()
                    size = 0
                    while True:
                        chunk = os.read(child_fd, 1024 * 1024)
                        if not chunk:
                            break
                        size += len(chunk)
                        digest.update(chunk)
                    final_info = os.fstat(child_fd)
                    require_same_metadata(opened_info, final_info, "tree-file-read")
                    if check_metadata(child_fd, final_info, False) != initial_file_xattrs:
                        fail(50, "tree-file-xattr-race")
                except OSError:
                    fail(50, "tree-read-file-failed")
                finally:
                    os.close(child_fd)
                require_same_metadata(child_info, lstat_child(fd, name, "tree-file-post"), "tree-file")
                if size != child_info.st_size:
                    fail(50, "tree-file-size-race")
                layout[child_path] = ("F", mode, size, digest.hexdigest())
            elif stat.S_ISLNK(child_info.st_mode):
                if child_info.st_nlink != 1:
                    fail(50, "tree-symlink-hardlink")
                try:
                    link_fd = os.open(name, os.O_RDONLY | O_SYMLINK_DARWIN, dir_fd=fd)
                except OSError:
                    fail(50, "tree-open-symlink-failed")
                try:
                    opened_info = os.fstat(link_fd)
                    require_same_metadata(child_info, opened_info, "tree-symlink-open")
                    if not stat.S_ISLNK(opened_info.st_mode):
                        fail(50, "tree-symlink-race")
                    initial_link_xattrs = check_metadata(link_fd, opened_info, True)
                    try:
                        link_text = os.readlink(name, dir_fd=fd)
                    except OSError:
                        fail(50, "tree-readlink-failed")
                    final_info = os.fstat(link_fd)
                    require_same_metadata(opened_info, final_info, "tree-symlink-read")
                    if check_metadata(link_fd, final_info, False) != initial_link_xattrs:
                        fail(50, "tree-symlink-xattr-race")
                finally:
                    os.close(link_fd)
                require_same_metadata(child_info, lstat_child(fd, name, "tree-symlink-post"), "tree-symlink")
                validate_ascii_field(link_text, "tree-link-text")
                if link_text.startswith("/"):
                    fail(50, "tree-absolute-link")
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(child_path), link_text))
                if not (resolved == "node_modules" or resolved.startswith("node_modules/")):
                    fail(50, "tree-escaping-link")
                layout[child_path] = ("L", mode, len(link_text.encode("utf-8")), link_text)
            else:
                fail(50, "tree-special-file")
        names_after = scan_names(fd)
        if names_after != names_before:
            fail(50, "tree-directory-entry-race")
        try:
            final = os.fstat(fd)
        except OSError:
            fail(50, "tree-directory-refstat-failed")
        require_same_metadata(initial, final, "tree-directory-read")
        if check_metadata(fd, final, False) != initial_xattrs:
            fail(50, "tree-directory-xattr-race")

    walk(root_fd, "node_modules")
    return layout, volatile_xattr_path_count


def public_summary(result):
    return {
        "profile_version": result["profile_version"],
        "package_json_sha256": result["package_json_sha256"],
        "package_lock_sha256": result["package_lock_sha256"],
        "lockfile_version": result["lockfile_version"],
        "lock_package_count": result["lock_package_count"],
        "selected_package_count": result["selected_package_count"],
        "excluded_platform_package_count": result["excluded_platform_package_count"],
        "compressed_bytes": result["compressed_bytes"],
        "tar_stream_bytes": result["tar_stream_bytes"],
        "payload_bytes": result["payload_bytes"],
        "raw_member_count": result["raw_member_count"],
        "raw_regular_count": result["raw_regular_count"],
        "raw_directory_count": result["raw_directory_count"],
        "bin_link_count": result["bin_link_count"],
        "lifecycle_field_count": result["lifecycle_field_count"],
        "content_receipt_body_bytes": result["content_receipt_body_bytes"],
        "content_receipt_sha256": result["content_receipt_sha256"],
        "ustar_closure_body_bytes": result["ustar_closure_body_bytes"],
        "ustar_closure_sha256": result["ustar_closure_sha256"],
        "resolution": result["resolution"],
        "tree": result["tree"],
    }


def derive_repo_root():
    script = os.path.realpath(__file__)
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script))))
    if not os.path.isdir(os.path.join(root, ".git")) and not os.path.isfile(os.path.join(root, ".git")):
        fail(20, "repo-root-shape")
    return root


def run(argv=None):
    parser = argparse.ArgumentParser(add_help=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    census_parser = subparsers.add_parser("census")
    census_parser.add_argument("--cache-root", required=True)
    verify_parser = subparsers.add_parser("verify-installed")
    verify_parser.add_argument("--cache-root", required=True)
    verify_parser.add_argument("--expected-tree-sha256", required=True)
    args = parser.parse_args(argv)
    repo_root = derive_repo_root()
    result = build_expected(repo_root, args.cache_root, retain_bytes=False)
    if args.command == "census":
        print(json.dumps(public_summary(result), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if args.expected_tree_sha256 != result["tree"]["sha256"]:
        fail(12, "expected-tree-digest-not-envelope-value")
    target = os.path.join(repo_root, "node_modules")
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        root_fd = os.open(target, flags)
    except OSError:
        fail(50, "node-modules-unavailable")
    try:
        actual_layout, volatile_xattr_path_count = fingerprint_tree_fd(root_fd)
    finally:
        os.close(root_fd)
    actual = layout_manifest(actual_layout)
    if actual != result["tree"] or actual_layout != result["layout"]:
        fail(50, "installed-tree-mismatch")
    output = {
        "state": "pass-static-attested-unexecuted",
        "tree": actual,
        "selected_package_count": result["selected_package_count"],
        "allowed_volatile_xattr_path_count": volatile_xattr_path_count,
        "openspec_execution_allowed": False,
        "openspec_scaffold_allowed": False,
    }
    print(json.dumps(output, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


def main():
    try:
        return run()
    except VerificationError as exc:
        print(
            json.dumps(
                {"state": "fail", "code": exc.code, "reason": exc.reason},
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return exc.code
    except Exception:
        print(
            '{"code":70,"reason":"internal-invariant","state":"fail"}',
            file=sys.stderr,
        )
        return 70


if __name__ == "__main__":
    sys.exit(main())
