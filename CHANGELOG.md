# CHANGELOG

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
**Method**: GET
**Description**: Returns both clean (without comments) and full (with comments) client configurations in a single request
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
**Method**: GET
**Description**: Now serves clean configuration (without comments) for direct download
**Response**: `text/plain` WireGuard configuration file
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