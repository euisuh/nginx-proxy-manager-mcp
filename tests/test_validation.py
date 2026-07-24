import pytest

from validation import (
    validate_access_clients,
    validate_domain_names,
    validate_forward_scheme,
    validate_host,
    validate_port,
    validate_positive_id,
    validate_redirect_code,
    validate_stream_protocols,
)


@pytest.mark.parametrize(
    "domains",
    [
        ["example.com"],
        ["www.example.com", "api.example.com"],
        ["*.example.com"],
    ],
)
def test_validate_domain_names_accepts_valid_domains(domains):
    assert validate_domain_names(domains) == domains


@pytest.mark.parametrize(
    "domains",
    [
        [],
        ["https://example.com"],
        ["example.com/path"],
        ["bad_label.example.com"],
        ["*bad.example.com"],
        ["example.com", "EXAMPLE.com"],
    ],
)
def test_validate_domain_names_rejects_invalid_domains(domains):
    with pytest.raises(ValueError):
        validate_domain_names(domains)


def test_validate_host_accepts_hostname_and_ip():
    assert validate_host("upstream.local", "forward_host") == "upstream.local"
    assert validate_host("192.168.1.10", "forward_host") == "192.168.1.10"


@pytest.mark.parametrize("host", ["https://host.local", "host.local/path", "*.example.com"])
def test_validate_host_rejects_urls_paths_and_wildcards(host):
    with pytest.raises(ValueError):
        validate_host(host, "forward_host")


@pytest.mark.parametrize("port", [1, 80, 65535])
def test_validate_port_accepts_valid_ports(port):
    assert validate_port(port) == port


@pytest.mark.parametrize("port", [0, 65536, -1, True, "80"])
def test_validate_port_rejects_invalid_ports(port):
    with pytest.raises(ValueError):
        validate_port(port)


@pytest.mark.parametrize("value", [1, 10])
def test_validate_positive_id_accepts_positive_ids(value):
    assert validate_positive_id(value) == value


@pytest.mark.parametrize("value", [0, -1, True, "1"])
def test_validate_positive_id_rejects_invalid_ids(value):
    with pytest.raises(ValueError):
        validate_positive_id(value)


@pytest.mark.parametrize("scheme", ["http", "https"])
def test_validate_forward_scheme_accepts_http_https(scheme):
    assert validate_forward_scheme(scheme) == scheme


@pytest.mark.parametrize("scheme", ["ftp", "", "HTTP"])
def test_validate_forward_scheme_rejects_unknown_scheme(scheme):
    with pytest.raises(ValueError):
        validate_forward_scheme(scheme)


@pytest.mark.parametrize("code", [300, 301, 302, 303, 307, 308])
def test_validate_redirect_code_accepts_known_redirects(code):
    assert validate_redirect_code(code) == code


@pytest.mark.parametrize("code", [200, 304, 400])
def test_validate_redirect_code_rejects_unknown_codes(code):
    with pytest.raises(ValueError):
        validate_redirect_code(code)


def test_validate_access_clients_accepts_ip_and_cidr():
    clients = [
        {"address": "203.0.113.10", "directive": "allow"},
        {"address": "2001:db8::/32", "directive": "deny"},
    ]
    assert validate_access_clients(clients) == clients


@pytest.mark.parametrize(
    "clients",
    [
        [{"address": "not-an-ip", "directive": "allow"}],
        [{"address": "203.0.113.10", "directive": "drop"}],
        ["203.0.113.10"],
    ],
)
def test_validate_access_clients_rejects_invalid_entries(clients):
    with pytest.raises(ValueError):
        validate_access_clients(clients)


def test_validate_stream_protocols_requires_tcp_or_udp():
    validate_stream_protocols(True, False)
    validate_stream_protocols(False, True)
    with pytest.raises(ValueError):
        validate_stream_protocols(False, False)
