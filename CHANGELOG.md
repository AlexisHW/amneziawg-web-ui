# CHANGELOG

## Version 1.6.4
### Fix
- Fixed full server config is not displayed if there are cyrillic letters in the server name

## Version 1.6.3
### Improvements
- Allow use of ranges in H1-H4 input fields
- Hide possibility to edit client name in client edit mode to avoid confusions.This functionality is not supported.

## Version 1.6.2
### Improvement
- Added conditional check if LE SSL config is already included. May be useful when container is stopped and restarted without recreation.

## Version 1.6.1
### Fix
- Fixed an issue for previously used client IPs of deleted clients are not properly assigned.

## Version 1.6.0
### New Features
- AmneziaWG 2.0 support (added parameters S3 and S4)


AWG 2.0 is **not compatible** with older versions, so to enable it, you have to recreate server and regenerate clients.

Previously created servers running on the updated app image **are not affected** and continue working in the `1.0/1.5` mode.

You have to use AmneziaVPN `4.8.12.7` client or newer or AmneziaWG `1.1.4` and newer to support AWG 2.0.

#### Technical info
In WireGuard, the Init packet is exactly 148 bytes, Response is 92 bytes, Cookie is 64 bytes, and Data has variable size (payload). AmneziaWG adds pseudorandom prefixes S1, S2, S3, and S4 (0 to 32/64 bytes) accordingly:

```
len(init) = 148 + random(0..S1)
len(resp) = 92 + random(0..S2)
len(cookie) = 64 + random(0..S3)
len(data) = payload + random(0..S4)
```

In WireGuard, Cookie Reply messages are used when the server is under load and issues cookie challenges (DoS mitigation). AmneziaWG obfuscates these packets like the other message types: the 32-bit message type is replaced with the configured magic header H3 (a value selected from the configured range), and then a random-length padding prefix of 0..S3 bytes is prepended (so the packet size becomes 64 + random(0..S3)).

With all parameters set to zero, behavior defaults to standard WireGuard — facilitating a smooth migration.

## Version 1.5.2
### Improvements
- UI was updated for a compact view.
- Create Test server button removed

## Version 1.5.1
### New Features
- For each client traffic, remote endpoint and last handshake time is displayed. Data is auto-refreshed every 5 seconds without API requests.

### Fix
- Fixed websocket polling issue with custom ports

## Version 1.5.0 - AWG 1.5 support
### New Features

- Added capability to configure I1-I5 settings for existing and new clients. This is a client-only configuration. In case awg 1.5 support is enabled but I-values are not provided, then only I1 default setting is applied which is recommended by AWG developers.

## Version 1.4.1 - IP range support
### New Features

- Now it's possible to limit connections to the web server with a IP range(s). Connections from the not allowed IP address will immediately get 403 reply.

## Version 1.4.0 - SSL support
### New Features

- SSL certificate generation at start and regular renewal support. Check [README.md](README.md).
- iptables-legacy support: if nft-iptables are not detected on host, then legacy iptables-legacy is set as default for running iptables command.

## Version 1.3.2 - obfuscation adjustment
### Fix
Minor fixes for generation of obfuscations params.
Adjusted default MTU.

### Improvement
Now Jmin and Jmax can be set manually in the valid ranges.
Improved params generation validation.


## Version 1.3.1 - healthcheck
### Fix
Fixed healthcheck on custom port. Added `/status` endpoint for health check.

## Version 1.3.0 - Client traffic
### New Features
Enables monitoring of per-client traffic statistics on a given server and displays the current traffic usage in the UI. After server is stopped the data on the network adapters is reset.

- Backend: Added `get_traffic_for_server` method to parse `awg show <interface>` output and map traffic to clients by public key.
- Backend: Added `/api/servers/<server_id>/traffic` endpoint returning traffic info JSON.
- Frontend: Modified `loadServerClients` to fetch traffic and pass it to renderServerClients.
- Frontend: Updated `renderServerClients` to display received and sent traffic per client below client IP.

### API Endpoints Added

#### `/api/servers/<server_id>/traffic`
**Method**: GET<br>
**Description**: This endpoint returns traffic statistics for all clients connected to a specified server.<br>
**Response Format**:
```json
{
  "clientA": {
    "received": "2.45 MiB",
    "sent": "5.12 MiB"
  },
  "clientB": {
    "received": "0 B",
    "sent": "0 B"
  }
}
```
If the server is not found or no traffic data is available, the endpoint returns:
```json
{
  "error": "Server not found or no traffic data"
}
```
with HTTP status code 404.


## Version 1.2.0 - QR Code Feature Release

### New Features
- **QR Code Generation**: Added QR code support for client configurations
- **Clean Config Format**: Implemented clean config generation without comments for QR codes
- **Dual Config Views**: Toggle between clean (QR-ready) and full (with comments) config views
- **QR Code Download**: Export QR codes as PNG images
- **Enhanced UI**: Improved modal design with better layout and responsive design
- **Configuration Toggle**: Switch between clean and full configuration views

### API Endpoints Added

#### 1. `/api/servers/<server_id>/clients/<client_id>/config-both`
**Method**: GET<br>
**Description**: Returns both clean (without comments) and full (with comments) client configurations in a single request<br>
**Response Format**:
```json
{
  "server_id": "abc123",
  "client_id": "xyz789",
  "client_name": "Client Name",
  "clean_config": "[Interface]\nPrivateKey = ...",
  "full_config": "# AmneziaWG Client Configuration\n[Interface]\n...",
  "clean_length": 450,
  "full_length": 600
}
```
**Purpose**: Optimized endpoint for QR code generation that returns both versions to reduce API calls

#### 2. Enhanced `/api/servers/<server_id>/clients/<client_id>/config`
**Method**: GET<br>
**Description**: Now serves clean configuration (without comments) for direct download<br>
**Response**: `text/plain` WireGuard configuration file<br>
**Changes**: Updated to use the unified `generate_wireguard_client_config()` function with `include_comments=True` parameter

### Client Configuration Endpoints

| Endpoint | Method | Description | Response Format |
|----------|--------|-------------|-----------------|
| `/api/servers/<server_id>/clients/<client_id>/config` | GET | Download client config (with comments) | `text/plain` (.conf file) |
| `/api/servers/<server_id>/clients/<client_id>/config-both` | GET | Get both clean and full configs | JSON with `clean_config` and `full_config` |
| `/api/servers/<server_id>/clients/<client_id>` | DELETE | Delete client | JSON status |

### Server Configuration Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/servers/<server_id>/info` | GET | Get server info with config preview |
| `/api/servers/<server_id>/config` | GET | Get raw server config |
| `/api/servers/<server_id>/config/download` | GET | Download server config file |

### Improvements:
- socket.io connection improvements on custom ports

## Version 1.1.1
Fix:
* clients are not applied to the running server when added without restart.
* clients are not properly removed from server config when removed from the app

## Version 1.1
Add: nginx basic auth support

## Version 1.0
Initial release