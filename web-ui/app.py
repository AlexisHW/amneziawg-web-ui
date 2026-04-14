#!/usr/bin/env python3
import os
import json
import subprocess
import tempfile
import uuid
import base64
import random
import requests
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_socketio import SocketIO
import threading
import time
import ipaddress

# Get the absolute path to the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Allowlisted log files for log endpoints
ALLOWED_LOG_FILES = [
    {"name": "Nginx Access", "path": "/var/log/nginx/access.log", "type": "access"},
    {"name": "Nginx Error", "path": "/var/log/nginx/error.log", "type": "error"},
    {"name": "Supervisor", "path": "/var/log/supervisor/supervisord.log", "type": "info"},
    {"name": "WebUI Access", "path": "/var/log/webui/access.log", "type": "access"},
    {"name": "WebUI Error", "path": "/var/log/webui/error.log", "type": "error"}
]
ALLOWED_LOG_PATHS = {log["path"] for log in ALLOWED_LOG_FILES}
ALLOWED_LOG_TYPES = {log["type"]: log["path"] for log in ALLOWED_LOG_FILES}
ALLOWED_LOG_REALPATHS = {os.path.realpath(path) for path in ALLOWED_LOG_PATHS}

def resolve_allowed_log_path(path_value):
    """Resolve and validate that a path is one of the explicitly allowlisted log files."""
    if not path_value:
        return None
    resolved_path = os.path.realpath(path_value)
    if resolved_path not in ALLOWED_LOG_REALPATHS:
        return None
    return resolved_path

# Essential environment variables
NGINX_PORT = os.getenv('NGINX_PORT', '80')
AUTO_START_SERVERS = os.getenv('AUTO_START_SERVERS', 'true').lower() == 'true'
DEFAULT_MTU = int(os.getenv('DEFAULT_MTU', '1280'))
DEFAULT_SUBNET = os.getenv('DEFAULT_SUBNET', '10.0.0.0/24')
DEFAULT_PORT = int(os.getenv('DEFAULT_PORT', '51820'))
DEFAULT_DNS = os.getenv('DEFAULT_DNS', '8.8.8.8,1.1.1.1')

# Parse DNS servers from comma-separated string
DNS_SERVERS = [dns.strip() for dns in DEFAULT_DNS.split(',') if dns.strip()]

# Fixed values for other settings
WEB_UI_PORT = 5000
CONFIG_DIR = '/etc/amnezia'
WIREGUARD_CONFIG_DIR = os.path.join(CONFIG_DIR, 'amneziawg')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'web_config.json')
PUBLIC_IP_SERVICE = 'http://ifconfig.me'
ENABLE_OBFUSCATION = True

DEFAULT_I1 = "<b 0xc70000000108ce1bf31eec7d93360000449e227e4596ed7f75c4d35ce31880b4133107c822c6355b51f0d7c1bba96d5c210a48aca01885fed0871cfc37d59137d73b506dc013bb4a13c060ca5b04b7ae215af71e37d6e8ff1db235f9fe0c25cb8b492471054a7c8d0d6077d430d07f6e87a8699287f6e69f54263c7334a8e144a29851429bf2e350e519445172d36953e96085110ce1fb641e5efad42c0feb4711ece959b72cc4d6f3c1e83251adb572b921534f6ac4b10927167f41fe50040a75acef62f45bded67c0b45b9d655ce374589cad6f568b8475b2e8921ff98628f86ff2eb5bcce6f3ddb7dc89e37c5b5e78ddc8d93a58896e530b5f9f1448ab3b7a1d1f24a63bf981634f6183a21af310ffa52e9ddf5521561760288669de01a5f2f1a4f922e68d0592026bbe4329b654d4f5d6ace4f6a23b8560b720a5350691c0037b10acfac9726add44e7d3e880ee6f3b0d6429ff33655c297fee786bb5ac032e48d2062cd45e305e6d8d8b82bfbf0fdbc5ec09943d1ad02b0b5868ac4b24bb10255196be883562c35a713002014016b8cc5224768b3d330016cf8ed9300fe6bf39b4b19b3667cddc6e7c7ebe4437a58862606a2a66bd4184b09ab9d2cd3d3faed4d2ab71dd821422a9540c4c5fa2a9b2e6693d411a22854a8e541ed930796521f03a54254074bc4c5bca152a1723260e7d70a24d49720acc544b41359cfc252385bda7de7d05878ac0ea0343c77715e145160e6562161dfe2024846dfda3ce99068817a2418e66e4f37dea40a21251c8a034f83145071d93baadf050ca0f95dc9ce2338fb082d64fbc8faba905cec66e65c0e1f9b003c32c943381282d4ab09bef9b6813ff3ff5118623d2617867e25f0601df583c3ac51bc6303f79e68d8f8de4b8363ec9c7728b3ec5fcd5274edfca2a42f2727aa223c557afb33f5bea4f64aeb252c0150ed734d4d8eccb257824e8e090f65029a3a042a51e5cc8767408ae07d55da8507e4d009ae72c47ddb138df3cab6cc023df2532f88fb5a4c4bd917fafde0f3134be09231c389c70bc55cb95a779615e8e0a76a2b4d943aabfde0e394c985c0cb0376930f92c5b6998ef49ff4a13652b787503f55c4e3d8eebd6e1bc6db3a6d405d8405bd7a8db7cefc64d16e0d105a468f3d33d29e5744a24c4ac43ce0eb1bf6b559aed520b91108cda2de6e2c4f14bc4f4dc58712580e07d217c8cca1aaf7ac04bab3e7b1008b966f1ed4fba3fd93a0a9d3a27127e7aa587fbcc60d548300146bdc126982a58ff5342fc41a43f83a3d2722a26645bc961894e339b953e78ab395ff2fb854247ad06d446cc2944a1aefb90573115dc198f5c1efbc22bc6d7a74e41e666a643d5f85f57fde81b87ceff95353d22ae8bab11684180dd142642894d8dc34e402f802c2fd4a73508ca99124e428d67437c871dd96e506ffc39c0fc401f666b437adca41fd563cbcfd0fa22fbbf8112979c4e677fb533d981745cceed0fe96da6cc0593c430bbb71bcbf924f70b4547b0bb4d41c94a09a9ef1147935a5c75bb2f721fbd24ea6a9f5c9331187490ffa6d4e34e6bb30c2c54a0344724f01088fb2751a486f425362741664efb287bce66c4a544c96fa8b124d3c6b9eaca170c0b530799a6e878a57f402eb0016cf2689d55c76b2a91285e2273763f3afc5bc9398273f5338a06d>"
DEFAULT_I2 = ""
DEFAULT_I3 = ""
DEFAULT_I4 = ""
DEFAULT_I5 = ""

print(f"Base directory: {BASE_DIR}")
print(f"Template directory: {TEMPLATE_DIR}")
print(f"Static directory: {STATIC_DIR}")
# Print environment configuration for debugging
print("=== Environment Configuration ===")
print(f"NGINX_PORT: {NGINX_PORT}")
print(f"AUTO_START_SERVERS: {AUTO_START_SERVERS}")
print(f"DEFAULT_MTU: {DEFAULT_MTU}")
print(f"DEFAULT_SUBNET: {DEFAULT_SUBNET}")
print(f"DEFAULT_PORT: {DEFAULT_PORT}")
print(f"DEFAULT_DNS: {DEFAULT_DNS}")
print(f"DNS_SERVERS: {DNS_SERVERS}")
print("==================================")
print("Fixed Configuration:")
print(f"WEB_UI_PORT: {WEB_UI_PORT} (internal)")
print(f"CONFIG_DIR: {CONFIG_DIR}")
print(f"ENABLE_OBFUSCATION: {ENABLE_OBFUSCATION}")
print("==================================")

# Check if directories exist
print(f"Templates exist: {os.path.exists(TEMPLATE_DIR)}")
print(f"Static exist: {os.path.exists(STATIC_DIR)}")
if os.path.exists(TEMPLATE_DIR):
    print(f"Template files: {os.listdir(TEMPLATE_DIR)}")
if os.path.exists(STATIC_DIR):
    print(f"Static files: {os.listdir(STATIC_DIR)}")

app = Flask(__name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)
app.secret_key = os.urandom(24)
socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins="*",  # Allow all origins for development
    path='/socket.io',
    ping_timeout=10,  # heatbeat default 20s
    ping_interval=15,  # Send ping every 15 seconds
    allow_upgrades=True,
    http_compression=True
)

class AmneziaManager:
    def __init__(self):
        self.config = self.load_config()
        self.ensure_directories()
        self.public_ip = self.detect_public_ip()
        self.traffic_update_interval = 5  # Update every 5 seconds

        # Auto-start servers based on environment variable
        if AUTO_START_SERVERS:
            self.auto_start_servers()
            
        self.start_traffic_updates()  # AUTO-START the traffic thread
        self.suspend_update_interval = 60  # Check every minute
        self.start_suspension_checker()  # Start scheduled suspension checker

    def ensure_directories(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(WIREGUARD_CONFIG_DIR, exist_ok=True)
        os.makedirs('/var/log/amnezia', exist_ok=True)

    def detect_public_ip(self):
        """Detect the public IP address of the server"""
        try:
            # Try multiple services in case one fails
            services = [
                'http://ifconfig.me',
                'https://api.ipify.org',
                'https://ident.me'
            ]

            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        if self.is_valid_ip(ip):
                            print(f"Detected public IP: {ip}")
                            return ip
                except:
                    continue

            # Fallback: try to get from network interfaces
            try:
                result = self.execute_command("ip route get 1 | awk '{print $7}' | head -1")
                if result and self.is_valid_ip(result):
                    print(f"Detected local IP: {result}")
                    return result
            except:
                pass

        except Exception as e:
            print(f"Failed to detect public IP: {e}")

        return "YOUR_SERVER_IP"  # Fallback

    def is_valid_ip(self, ip):
        """Check if the string is a valid IP address"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False

    def auto_start_servers(self):
        """Auto-start servers that have config files and were running before"""
        print("Checking for existing servers to auto-start...")
        for server in self.config["servers"]:
            if os.path.exists(server['config_path']):
                current_status = self.get_server_status(server['id'])
                if current_status == 'stopped' and server.get('auto_start', True):
                    print(f"Auto-starting server: {server['name']}")
                    self.start_server(server['id'])

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {"servers": [], "clients": {}}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)

    def execute_command(self, command):
        """Execute shell command and return result"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")
            return None

    def generate_wireguard_keys(self):
        """Generate real WireGuard keys"""
        try:
            private_key = self.execute_command("awg genkey")
            if private_key:
                public_key = self.execute_command(f"echo '{private_key}' | awg pubkey")
                return {
                    "private_key": private_key,
                    "public_key": public_key
                }
        except Exception as e:
            print(f"Key generation failed: {e}")

        # Fallback - generate random keys
        fake_private = base64.b64encode(os.urandom(32)).decode('utf-8')
        fake_public = base64.b64encode(os.urandom(32)).decode('utf-8')
        return {
            "private_key": fake_private,
            "public_key": fake_public
        }

    def generate_preshared_key(self):
        """Generate preshared key"""
        try:
            return self.execute_command("awg genpsk")
        except:
            return base64.b64encode(os.urandom(32)).decode('utf-8')

    def generate_obfuscation_params(self, mtu=1420):
        import random
        S1 = random.randint(15, min(150, mtu - 148))
        # S2 must not be S1+56
        s2_candidates = [s for s in range(15, min(150, mtu - 92) + 1) if s != S1 + 56]
        S2 = random.choice(s2_candidates)
        S3 = random.randint(1, 256)
        S4 = random.randint(1, 32)
        Jmin = random.randint(4, mtu - 2)
        Jmax = random.randint(Jmin + 1, mtu)
        return {
            "Jc": random.randint(4, 12),
            "Jmin": Jmin,
            "Jmax": Jmax,
            "S1": S1,
            "S2": S2,
            "S3": S3,
            "S4": S4,
            "H1": random.randint(10000, 100000),
            "H2": random.randint(100000, 200000),
            "H3": random.randint(200000, 300000),
            "H4": random.randint(300000, 400000),
            "MTU": mtu
        }

    def create_wireguard_server(self, server_data):
        """Create a new WireGuard server configuration with environment defaults"""
        server_name = server_data.get('name', 'New Server')
        port = server_data.get('port', DEFAULT_PORT)
        subnet = server_data.get('subnet', DEFAULT_SUBNET)
        mtu = server_data.get('mtu', DEFAULT_MTU)

        # Get DNS servers from request or use environment default
        custom_dns = server_data.get('dns')
        if custom_dns:
            # Parse custom DNS from request
            if isinstance(custom_dns, str):
                dns_servers = [dns.strip() for dns in custom_dns.split(',') if dns.strip()]
            elif isinstance(custom_dns, list):
                dns_servers = custom_dns
            else:
                dns_servers = DNS_SERVERS
        else:
            dns_servers = DNS_SERVERS

        # Validate MTU
        if mtu < 1280 or mtu > 1440:
            raise ValueError(f"MTU must be between 1280 and 1440, got {mtu}")

        # Validate DNS servers
        for dns in dns_servers:
            if not self.is_valid_ip(dns):
                raise ValueError(f"Invalid DNS server IP: {dns}")

        # Fixed values for other settings
        enable_obfuscation = server_data.get('obfuscation', ENABLE_OBFUSCATION)
        auto_start = server_data.get('auto_start', AUTO_START_SERVERS)

        server_id = str(uuid.uuid4())[:6]
        interface_name = f"wg-{server_id}"
        config_path = os.path.join(WIREGUARD_CONFIG_DIR, f"{interface_name}.conf")

        # Generate server keys
        server_keys = self.generate_wireguard_keys()

        # Generate and use provided obfuscation parameters if enabled
        obfuscation_params = None
        if enable_obfuscation:
            if 'obfuscation_params' in server_data:
                obfuscation_params = server_data['obfuscation_params']
            else:
                obfuscation_params = self.generate_obfuscation_params(mtu)
                
        awg2_enabled = server_data.get('awg2', False)

        # Parse subnet for server IP
        subnet_parts = subnet.split('/')
        network = subnet_parts[0]
        prefix = subnet_parts[1] if len(subnet_parts) > 1 else "24"
        server_ip = self.get_server_ip(network)

        # Create WireGuard server configuration
        server_config_content = f"""[Interface]
PrivateKey = {server_keys['private_key']}
Address = {server_ip}/{prefix}
ListenPort = {port}
SaveConfig = false
MTU = {mtu}
"""

        # Add obfuscation parameters if enabled
        if enable_obfuscation and obfuscation_params:
            server_config_content += f"""Jc = {obfuscation_params['Jc']}
Jmin = {obfuscation_params['Jmin']}
Jmax = {obfuscation_params['Jmax']}
S1 = {obfuscation_params['S1']}
S2 = {obfuscation_params['S2']}
"""
            if awg2_enabled:
                server_config_content += f"""S3 = {obfuscation_params['S3']}
S4 = {obfuscation_params['S4']}
"""
            server_config_content += f"""H1 = {obfuscation_params['H1']}
H2 = {obfuscation_params['H2']}
H3 = {obfuscation_params['H3']}
H4 = {obfuscation_params['H4']}
"""

        server_config = {
            "id": server_id,
            "name": server_name,
            "protocol": "wireguard",
            "port": port,
            "status": "stopped",
            "interface": interface_name,
            "config_path": config_path,
            "server_public_key": server_keys['public_key'],
            "server_private_key": server_keys['private_key'],
            "subnet": subnet,
            "server_ip": server_ip,
            "mtu": mtu,
            "public_ip": self.public_ip,
            "obfuscation_enabled": enable_obfuscation,
            "awg2_enabled": awg2_enabled,
            "obfuscation_params": obfuscation_params,
            "auto_start": auto_start,
            "dns": dns_servers,  # Store DNS servers
            "clients": [],
            "unbound_nat_ips": [],
            "created_at": time.time()
        }

        # Save WireGuard config file
        with open(config_path, 'w') as f:
            f.write(server_config_content)

        self.config["servers"].append(server_config)
        self.save_config()

        # Auto-start if enabled (from environment or request)
        if auto_start:
            print(f"Auto-starting new server: {server_name}")
            self.start_server(server_id)

        return server_config
    
    def apply_live_config(self, interface):
        """Apply the latest config to the running WireGuard interface using wg syncconf."""
        try:
            # Use bash -c to support process substitution
            command = f"bash -c 'awg syncconf {interface} <(awg-quick strip {interface})'"
            result = self.execute_command(command)
            if result is not None:
                print(f"Live config applied to {interface}")
                return True
            else:
                print(f"Failed to apply live config to {interface}")
                return False
        except Exception as e:
            print(f"Error applying live config to {interface}: {e}")
            return False

    def get_server_ip(self, network):
        """Get server IP from network (first usable IP)"""
        parts = network.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.1"
        return "10.0.0.1"

    def get_new_client_ip(self, server_id):
        """Get client IP from server subnet"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return False

        unbound_ips = server.get("unbound_nat_ips", [])
        if unbound_ips:
            unbound_ip = unbound_ips.pop(0)
            server["unbound_nat_ips"] = unbound_ips
            self.save_config()
            return unbound_ip

        subnet_str = server['subnet']
        network = ipaddress.ip_network(subnet_str)
    
        used_ips = {server['server_ip']}
        for client in server.get('clients', []):
            used_ips.add(client['client_ip'])

        for ip in network.hosts():
            ip_str = str(ip)
            if ip_str not in used_ips:
                return ip_str

        print(f"Subnet {subnet_str} is full! No available IPs.")
        return False

    def delete_server(self, server_id):
        """Delete a server and all its clients"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return False

        # Stop the server if running
        if server['status'] == 'running':
            self.stop_server(server_id)

        # Remove config file
        if os.path.exists(server['config_path']):
            os.remove(server['config_path'])

        # Remove all clients associated with this server
        self.config["clients"] = {k: v for k, v in self.config["clients"].items()
                                if v.get("server_id") != server_id}

        # Remove the server
        self.config["servers"] = [s for s in self.config["servers"] if s["id"] != server_id]
        self.save_config()
        return True

    def add_wireguard_client(self, server_id, client_name, apply_i_settings=False, i_settings=None):
        """Add a client to a WireGuard server with optional I-settings"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return None

        client_id = str(uuid.uuid4())[:6]

        # Generate client keys
        client_keys = self.generate_wireguard_keys()
        preshared_key = self.generate_preshared_key()

        # Assign client IP
        client_ip = self.get_new_client_ip(server_id)
        if not client_ip:
            return None

        # Process I-settings
        client_i_settings = {}
        if apply_i_settings:
            # Start with defaults
            client_i_settings = {
                'i1': DEFAULT_I1,
                'i2': DEFAULT_I2,
                'i3': DEFAULT_I3,
                'i4': DEFAULT_I4,
                'i5': DEFAULT_I5,
            }
            
            # Override with provided values
            if i_settings:
                for i in range(1, 6):
                    i_key = f'i{i}'
                    if i_key in i_settings and i_settings[i_key]:
                        client_i_settings[i_key] = i_settings[i_key]

        client_config = {
            "id": client_id,
            "name": client_name,
            "server_id": server_id,
            "server_name": server["name"],
            "status": "active",  # Set initial status to active
            "created_at": time.time(),
            "client_private_key": client_keys["private_key"],
            "client_public_key": client_keys["public_key"],
            "preshared_key": preshared_key,
            "client_ip": client_ip,
            "obfuscation_enabled": server["obfuscation_enabled"],
            "obfuscation_params": server["obfuscation_params"],
            "apply_i_settings": apply_i_settings,
            "i_settings": client_i_settings,
            "awg2_enabled": server.get("awg2_enabled", False)
        }

        # Add client to server config
        client_peer_config = f"""
# Client: {client_config['name']}
[Peer]
PublicKey = {client_keys['public_key']}
PresharedKey = {preshared_key}
AllowedIPs = {client_ip}/32
"""

        # Append client to server config file
        with open(server['config_path'], 'a') as f:
            f.write(client_peer_config)

        # Add to server's clients list
        server["clients"].append(client_config)

        # Also add to global clients dict
        self.config["clients"][client_id] = client_config.copy()
        
        self.save_config()
        
        # Apply live config if server is running
        if server['status'] == 'running':
            self.apply_live_config(server['interface'])
            
        print(f"Client {client_config['name']} added")

        config_content = self.generate_wireguard_client_config(server, client_config, include_comments=True)
        return client_config, config_content

    def delete_client(self, server_id, client_id):
        """Delete a client from a server and update the config file"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return False

        client = next((c for c in server["clients"] if c["id"] == client_id), None)
        if not client:
            return False

        # Remove client from server's client list
        server["clients"] = [c for c in server["clients"] if c["id"] != client_id]

        # Remove from global clients dict
        if client_id in self.config["clients"]:
            del self.config["clients"][client_id]

        server.setdefault("unbound_nat_ips", []).append(client["client_ip"])

        # Rewrite the config file without the deleted client's [Peer] block
        self.rewrite_server_conf_without_client(server, client)

        self.save_config()

        # Apply live config if server is running
        if server['status'] == 'running':
            self.apply_live_config(server['interface'])
            
        print(f"Client {server['name']}:{client['name']} removed")

        return True
    
    def rewrite_server_conf_without_client(self, server, client):
        """Rewrite the server conf file without the specified client's [Peer] block"""
        if not os.path.exists(server['config_path']):
            return

        with open(server['config_path'], 'r') as f:
            lines = f.readlines()

        new_lines = []
        skip = False
        client_marker = f"# Client: {client['name']}"

        for line in lines:
            stripped = line.strip()

            # Start skipping when we find the client marker line
            if stripped == client_marker:
                skip = True
                continue

            # Stop skipping when we hit the next client marker line
            if skip and stripped.startswith("# Client:"):
                skip = False

            # If skipping, skip all lines until next client marker
            if skip:
                continue

            # Otherwise, keep the line
            new_lines.append(line)

        # Remove trailing blank lines if any
        while new_lines and new_lines[-1].strip() == '':
            new_lines.pop()

        with open(server['config_path'], 'w') as f:
            f.writelines(new_lines)

    def generate_wireguard_client_config(self, server, client_config, include_comments=True):
        """Generate WireGuard client configuration with optional I-settings"""
        config = ""
        
        # Add comments only if requested
        if include_comments:
            config = f"""# AmneziaWG Client Configuration
# Server: {server['name']}
# Client: {client_config['name']}
# Generated: {time.ctime(client_config['created_at'])}
# Server IP: {server['public_ip']}:{server['port']}
"""

        config += f"""[Interface]
PrivateKey = {client_config['client_private_key']}
Address = {client_config['client_ip']}/32
DNS = {', '.join(server['dns'])}
MTU = {server['mtu']}
"""

        # Add obfuscation parameters if enabled
        if client_config.get('obfuscation_enabled', False) and client_config.get('obfuscation_params'):
            params = client_config['obfuscation_params']
            config += f"""Jc = {params['Jc']}
Jmin = {params['Jmin']}
Jmax = {params['Jmax']}
S1 = {params['S1']}
S2 = {params['S2']}
"""
            if client_config.get('awg2_enabled', False):
                config += f"""S3 = {params['S3']}
S4 = {params['S4']}
"""
            config += f"""H1 = {params['H1']}
H2 = {params['H2']}
H3 = {params['H3']}
H4 = {params['H4']}
"""

        # Add I-settings if enabled and I1 is present
        if client_config.get('apply_i_settings', False):
            i_settings = client_config.get('i_settings', {})
            i1_value = i_settings.get('i1', '')
            
            if i1_value:  # Only add I-settings if I1 is present
                for i in range(1, 6):
                    i_value = i_settings.get(f'i{i}', '')
                    if i_value:  # Only add non-empty values
                        config += f"I{i} = {i_value}\n"
        
        config += f"""
[Peer]
PublicKey = {server['server_public_key']}
PresharedKey = {client_config['preshared_key']}
Endpoint = {server['public_ip']}:{server['port']}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
        return config
    
    def update_client_i_settings(self, server_id, client_id, apply_i_settings=None, i_settings=None):
        """Update client I-settings"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return None, "Server not found"

        # Find client in server's client list
        client = None
        for c in server["clients"]:
            if c["id"] == client_id:
                client = c
                break
        
        if not client:
            return None, "Client not found"
        
        # Update apply_i_settings if provided
        if apply_i_settings is not None:
            client['apply_i_settings'] = apply_i_settings
            if client_id in self.config["clients"]:
                self.config["clients"][client_id]['apply_i_settings'] = apply_i_settings
        
        # Process I-settings
        if i_settings is not None:
            new_i_settings = {}
            
            if apply_i_settings or client.get('apply_i_settings', False):
                # Start with defaults
                new_i_settings = {
                    'i1': DEFAULT_I1,
                    'i2': DEFAULT_I2,
                    'i3': DEFAULT_I3,
                    'i4': DEFAULT_I4,
                    'i5': DEFAULT_I5,
                }
                
                # Override with provided values
                for i in range(1, 6):
                    i_key = f'i{i}'
                    if i_key in i_settings and i_settings[i_key]:
                        new_i_settings[i_key] = i_settings[i_key]
                    elif client.get('i_settings', {}).get(i_key):
                        # Keep existing value
                        new_i_settings[i_key] = client['i_settings'][i_key]
            
            # Update both client objects
            client['i_settings'] = new_i_settings
            if client_id in self.config["clients"]:
                self.config["clients"][client_id]['i_settings'] = new_i_settings.copy()
        
        self.save_config()
        
        # Regenerate config
        config_content = self.generate_wireguard_client_config(server, client, include_comments=True)
        
        return client, config_content
    
    def suspend_client(self, server_id, client_id):
        """Suspend a client by removing its config from the main file"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return False, "Server not found"

        client = next((c for c in server["clients"] if c["id"] == client_id), None)
        if not client:
            return False, "Client not found"

        # Create suspended configs directory if it doesn't exist
        suspended_dir = os.path.join(WIREGUARD_CONFIG_DIR, 'suspended')
        os.makedirs(suspended_dir, exist_ok=True)

        # Extract and save the client's peer block to suspended directory
        if os.path.exists(server['config_path']):
            with open(server['config_path'], 'r') as f:
                content = f.read()

            # Find the client's peer block
            client_marker = f"# Client: {client['name']}"
            lines = content.split('\n')
            
            peer_block = []
            in_peer_block = False
            for i, line in enumerate(lines):
                if line.strip() == client_marker:
                    in_peer_block = True
                    peer_block.append(line)
                elif in_peer_block and line.strip().startswith('[Peer]'):
                    peer_block.append(line)
                elif in_peer_block and line.strip() and not line.strip().startswith('#'):
                    peer_block.append(line)
                elif in_peer_block and not line.strip():
                    peer_block.append(line)
                    break

            if peer_block:
                suspended_path = os.path.join(suspended_dir, f"{client_id}.conf")
                with open(suspended_path, 'w') as f:
                    f.write('\n'.join(peer_block))

        # Remove client from server config
        self.rewrite_server_conf_without_client(server, client)
        
        # Update client status
        client['status'] = 'suspended'
        if client_id in self.config["clients"]:
            self.config["clients"][client_id]['status'] = 'suspended'

        self.save_config()

        # Apply live config if server is running
        if server['status'] == 'running':
            self.apply_live_config(server['interface'])

        return True, "Client suspended successfully"

    def activate_client(self, server_id, client_id):
        """Activate a suspended client by restoring its config"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return False, "Server not found"

        client = next((c for c in server["clients"] if c["id"] == client_id), None)
        if not client:
            return False, "Client not found"

        # Check if client is suspended
        if client.get('status') != 'suspended':
            return False, "Client is not suspended"

        # Check for suspended config file
        suspended_dir = os.path.join(WIREGUARD_CONFIG_DIR, 'suspended')
        suspended_path = os.path.join(suspended_dir, f"{client_id}.conf")

        if not os.path.exists(suspended_path):
            return False, "Suspended config file not found"

        # Read the suspended config
        with open(suspended_path, 'r') as f:
            suspended_config = f.read()

        # Append config back to server config
        with open(server['config_path'], 'a') as f:
            f.write('\n' + suspended_config)

        # Remove suspended config file
        os.remove(suspended_path)

        # Update client status
        client['status'] = 'active'
        if client_id in self.config["clients"]:
            self.config["clients"][client_id]['status'] = 'active'

        self.save_config()

        # Apply live config if server is running
        if server['status'] == 'running':
            self.apply_live_config(server['interface'])

        return True, "Client activated successfully"
    
    def start_suspension_checker(self):
        """Start background task to check scheduled suspensions"""
        def check_suspensions():
            while True:
                try:
                    current_time = time.time()
                    for server in self.config['servers']:
                        for client in server['clients']:
                            suspend_at = client.get('suspend_at')
                            if suspend_at and client.get('status') == 'active':
                                if current_time >= suspend_at:
                                    # Reuse existing suspend endpoint logic
                                    self.suspend_client(server['id'], client['id'])
                                    print(f"Auto-suspended client {client['name']} at {time.ctime()}")
                except Exception as e:
                    print(f"Error checking suspensions: {e}")
                time.sleep(self.suspend_update_interval)
        
        suspension_thread = threading.Thread(target=check_suspensions, daemon=True)
        suspension_thread.start()

    def update_client_suspend_time(self, server_id, client_id, suspend_at=None):
        """Update client suspension time (without actually suspending)"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return None, "Server not found"

        client = next((c for c in server["clients"] if c["id"] == client_id), None)
        if not client:
            return None, "Client not found"
        
        # Update suspension time
        if suspend_at:
            client['suspend_at'] = suspend_at
        else:
            client.pop('suspend_at', None)
        
        # Update global clients dict
        if client_id in self.config["clients"]:
            if suspend_at:
                self.config["clients"][client_id]['suspend_at'] = suspend_at
            else:
                self.config["clients"][client_id].pop('suspend_at', None)
        
        self.save_config()
        return client, "Suspension time updated"

    def setup_iptables(self, interface, subnet):
        """Setup iptables rules for WireGuard interface"""
        try:
            script_path = "/app/scripts/setup_iptables.sh"
            if os.path.exists(script_path):
                result = self.execute_command(f"{script_path} {interface} {subnet}")
                if result is not None:
                    print(f"iptables setup completed for {interface}")
                    return True
                else:
                    print(f"iptables setup failed for {interface}")
                    return False
            else:
                print(f"iptables script not found at {script_path}")
                return False
        except Exception as e:
            print(f"Error setting up iptables for {interface}: {e}")
            return False

    def cleanup_iptables(self, interface, subnet):
        """Cleanup iptables rules for WireGuard interface"""
        try:
            script_path = "/app/scripts/cleanup_iptables.sh"
            if os.path.exists(script_path):
                result = self.execute_command(f"{script_path} {interface} {subnet}")
                if result is not None:
                    print(f"iptables cleanup completed for {interface}")
                    return True
                else:
                    print(f"iptables cleanup failed for {interface}")
                    return False
            else:
                print(f"iptables cleanup script not found at {script_path}")
                return False
        except Exception as e:
            print(f"Error cleaning up iptables for {interface}: {e}")
            return False

    def start_server(self, server_id):
        """Start a WireGuard server using awg-quick with iptables setup"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return False

        try:
            # Use awg-quick to bring up the interface
            result = self.execute_command(f"/usr/bin/awg-quick up {server['interface']}")
            if result is not None:
                # Setup iptables rules
                iptables_success = self.setup_iptables(server['interface'], server['subnet'])

                server['status'] = 'running'
                self.save_config()

                print(f"Server {server['name']} started successfully")
                if iptables_success:
                    print(f"iptables rules configured for {server['interface']}")
                else:
                    print(f"Warning: iptables setup may have failed for {server['interface']}")

                threading.Thread(target=self.simulate_server_operation, args=(server_id, 'running')).start()
                return True
            else:
                print(f"Failed to start server {server['name']}")
        except Exception as e:
            print(f"Failed to start server {server_id}: {e}")

        return False

    def stop_server(self, server_id):
        """Stop a WireGuard server using awg-quick with iptables cleanup"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return False

        try:
            # Cleanup iptables rules first
            iptables_cleaned = self.cleanup_iptables(server['interface'], server['subnet'])

            # Use awg-quick to bring down the interface
            result = self.execute_command(f"/usr/bin/awg-quick down {server['interface']}")
            if result is not None:
                server['status'] = 'stopped'
                self.save_config()

                print(f"Server {server['name']} stopped successfully")
                if iptables_cleaned:
                    print(f"iptables rules cleaned up for {server['interface']}")

                threading.Thread(target=self.simulate_server_operation, args=(server_id, 'stopped')).start()
                return True
            else:
                print(f"Failed to stop server {server['name']}")
        except Exception as e:
            print(f"Failed to stop server {server_id}: {e}")

        return False

    def get_server_status(self, server_id):
        """Check actual server status by checking interface"""
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return "not_found"

        try:
            # Check if interface exists and is up
            result = subprocess.run(["ip", "link", "show", server['interface']], capture_output=True, text=True)
            if "state UNKNOWN" in result.stdout:
                return "running"
            else:
                print(f"Server {server['interface']} currently stopped")
                return "stopped"
        except:
            return "stopped"

    def simulate_server_operation(self, server_id, status):
        """Simulate server operation with status updates"""
        time.sleep(2)
        socketio.emit('server_status', {
            'server_id': server_id,
            'status': status
        })

    def get_client_configs(self, server_id=None):
        """Get all client configs, optionally filtered by server"""
        if server_id:
            # Get from specific server
            server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
            if server:
                return server['clients']
            return []
        else:
            # Get all clients from global dict
            clients = []
            for client_id, client in self.config["clients"].items():
                client_copy = client.copy()
                if 'apply_i_settings' not in client_copy:
                    client_copy['apply_i_settings'] = False
                if 'i_settings' not in client_copy:
                    client_copy['i_settings'] = {}
                clients.append(client_copy)
                if 'status' not in client_copy:
                    client_copy['status'] = 'active'
            return clients

    def get_peer_traffic_for_server(self, server_id):
        server = next((s for s in self.config['servers'] if s['id'] == server_id), None)
        if not server:
            return None

        interface = server['interface']
        output = self.execute_command(f"/usr/bin/awg show {interface}")
        if not output:
            return None

        # Parse output to get traffic and handshake per peer public key
        peer_data = {}

        lines = output.splitlines()
        current_peer = None
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("peer:"):
                current_peer = line.split("peer:")[1].strip()
                peer_data[current_peer] = {
                    "received": "0 B",
                    "sent": "0 B",
                    "last_handshake": "Never",
                    "endpoint": "",
                    "latest_handshake_epoch": 0
                }
            
            elif line.startswith("transfer:") and current_peer:
                # transfer: 1.39 MiB received, 6.59 MiB sent
                transfer_line = line[len("transfer:"):].strip()
                parts = transfer_line.split(',')
                received = parts[0].strip() if len(parts) > 0 else "0 B"
                sent = parts[1].strip() if len(parts) > 1 else "0 B"
                
                if current_peer in peer_data:
                    peer_data[current_peer]["received"] = received
                    peer_data[current_peer]["sent"] = sent
            
            elif line.startswith("endpoint:") and current_peer:
                endpoint = line.split("endpoint:")[1].strip()
                if current_peer in peer_data:
                    peer_data[current_peer]["endpoint"] = endpoint
            
            elif line.startswith("allowed ips:") and current_peer:
                allowed_ips = line.split("allowed ips:")[1].strip()
                if current_peer in peer_data:
                    peer_data[current_peer]["allowed_ips"] = allowed_ips
            
            elif line.startswith("latest handshake:") and current_peer:
                # latest handshake: 1 minute, 23 seconds ago
                # or: latest handshake: 5 hours, 12 minutes ago
                # or: latest handshake: 2 days, 3 hours ago
                handshake_line = line[len("latest handshake:"):].strip()
                
                if current_peer in peer_data:
                    peer_data[current_peer]["last_handshake"] = handshake_line
                    
                    # Also parse to epoch seconds if available
                    try:
                        # Try to get raw handshake time (might be in different format)
                        if handshake_line != "Never":
                            # Parse relative time to approximate epoch
                            import re
                            import time
                            
                            total_seconds = 0
                            # Parse format like "1 minute, 23 seconds ago"
                            parts = handshake_line.replace(' ago', '').split(', ')
                            for part in parts:
                                match = re.match(r'(\d+)\s+(\w+)', part)
                                if match:
                                    value = int(match.group(1))
                                    unit = match.group(2)
                                    if unit.startswith('second'):
                                        total_seconds += value
                                    elif unit.startswith('minute'):
                                        total_seconds += value * 60
                                    elif unit.startswith('hour'):
                                        total_seconds += value * 3600
                                    elif unit.startswith('day'):
                                        total_seconds += value * 86400
                            
                            peer_data[current_peer]["latest_handshake_epoch"] = time.time() - total_seconds
                    except:
                        peer_data[current_peer]["latest_handshake_epoch"] = 0
            
            i += 1

        # Map data to clients by matching public keys
        clients_data = {}
        for client_id, client in self.config["clients"].items():
            if client.get("server_id") == server_id:
                pubkey = client.get("client_public_key")
                if pubkey in peer_data:
                    clients_data[client_id] = {
                        "received": peer_data[pubkey]["received"],
                        "sent": peer_data[pubkey]["sent"],
                        "last_handshake": peer_data[pubkey]["last_handshake"],
                        "endpoint": peer_data[pubkey]["endpoint"]
                    }
                else:
                    clients_data[client_id] = {
                        "received": "0 B",
                        "sent": "0 B",
                        "last_handshake": "Never",
                        "endpoint": ""
                    }

        return clients_data
    
    def get_server_interface_traffic(self, interface_name):
        """Get RX/TX traffic for a server interface using ifconfig"""
        try:
            result = self.execute_command(f"ifconfig {interface_name}")
            if not result:
                return None
            
            rx_bytes = "0 B"
            tx_bytes = "0 B"
            
            lines = result.split('\n')
            for line in lines:
                line = line.strip()
                
                if 'RX bytes:' in line:
                    import re
                    match = re.search(r'RX bytes:\d+\s+\(([^)]+)\)', line)
                    if match:
                        rx_bytes = match.group(1).strip()
                
                if 'TX bytes:' in line:
                    import re
                    match = re.search(r'TX bytes:\d+\s+\(([^)]+)\)', line)
                    if match:
                        tx_bytes = match.group(1).strip()
            
            return {
                "rx": rx_bytes,
                "tx": tx_bytes
            }
        except Exception as e:
            print(f"Error getting interface traffic for {interface_name}: {e}")
            return None

    def get_all_servers_traffic(self):
        """Get interface traffic for all servers"""
        servers_traffic = {}
        for server in self.config['servers']:
            interface = server.get('interface')
            if interface:
                traffic = self.get_server_interface_traffic(interface)
                if traffic:
                    servers_traffic[server['id']] = traffic
        return servers_traffic

    def start_traffic_updates(self):
        """Start traffic updates using SocketIO background task"""
        def update_traffic():
            while True:
                try:
                    # Get client traffic
                    all_client_traffic = {}
                    for server in self.config['servers']:
                        server_id = server['id']
                        traffic = self.get_peer_traffic_for_server(server_id)
                        if traffic:
                            all_client_traffic[server_id] = traffic
                    
                    # Get server interface traffic
                    server_interface_traffic = self.get_all_servers_traffic()
                    
                    # Send combined data in clean format
                    if all_client_traffic or server_interface_traffic:
                        socketio.emit('traffic_update', {
                            'timestamp': time.time(),
                            'client_traffic': all_client_traffic,
                            'server_traffic': server_interface_traffic
                        })
                    
                except Exception as e:
                    print(f"Traffic update error: {e}")
                
                socketio.sleep(self.traffic_update_interval)
        
        socketio.start_background_task(update_traffic)

amnezia_manager = AmneziaManager()

# API Routes
@app.route('/')
def index():
    print("Serving index.html")
    return render_template('index.html')

# Explicit static file route to ensure they're served
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route('/api/servers', methods=['POST'])
def create_server():
    data = request.json
    server = amnezia_manager.create_wireguard_server(data)
    return jsonify(server)

@app.route('/api/servers/<server_id>', methods=['DELETE'])
def delete_server(server_id):
    if amnezia_manager.delete_server(server_id):
        return jsonify({"status": "deleted", "server_id": server_id})
    return jsonify({"error": "Server not found"}), 404

@app.route('/api/servers/<server_id>/start', methods=['POST'])
def start_server(server_id):
    if amnezia_manager.start_server(server_id):
        return jsonify({"status": "started"})
    return jsonify({"error": "Server not found or failed to start"}), 404

@app.route('/api/servers/<server_id>/stop', methods=['POST'])
def stop_server(server_id):
    if amnezia_manager.stop_server(server_id):
        return jsonify({"status": "stopped"})
    return jsonify({"error": "Server not found or failed to stop"}), 404

@app.route('/api/servers/<server_id>/clients', methods=['GET'])
def get_server_clients(server_id):
    clients = amnezia_manager.get_client_configs(server_id)
    return jsonify(clients)

@app.route('/api/servers/<server_id>/clients', methods=['POST'])
def add_client(server_id):
    data = request.json
    client_name = data.get('name', 'New Client')
    apply_i_settings = data.get('apply_i_settings', False)
    i_settings = data.get('i_settings', {})

    result = amnezia_manager.add_wireguard_client(server_id, client_name, apply_i_settings, i_settings)
    if result:
        client_config, config_content = result
        return jsonify({
            "client": client_config,
            "config": config_content
        })
    return jsonify({"error": "Server not found"}), 404

@app.route('/api/servers/<server_id>/clients/<client_id>', methods=['DELETE'])
def delete_client(server_id, client_id):
    if amnezia_manager.delete_client(server_id, client_id):
        return jsonify({"status": "deleted", "client_id": client_id})
    return jsonify({"error": "Client not found"}), 404

@app.route('/api/servers/<server_id>/clients/<client_id>/i-settings', methods=['PUT'])
def update_client_i_settings(server_id, client_id):
    data = request.json
    apply_i_settings = data.get('apply_i_settings')
    i_settings = data.get('i_settings', {})
    
    client, config_content = amnezia_manager.update_client_i_settings(
        server_id, client_id, apply_i_settings, i_settings
    )
    
    if client:
        return jsonify({
            "client": client,
            "config": config_content
        })
    return jsonify({"error": "Client not found"}), 404

@app.route('/api/servers/<server_id>/clients/<client_id>/config')
def download_client_config(server_id, client_id):
    """Download client configuration file (with comments)"""
    client = amnezia_manager.config["clients"].get(client_id)
    if not client or client.get("server_id") != server_id:
        return jsonify({"error": "Client not found"}), 404

    server = next((s for s in amnezia_manager.config['servers'] if s['id'] == server_id), None)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    # Use full version with comments for download
    config_content = amnezia_manager.generate_wireguard_client_config(
        server, client, include_comments=True
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    filename = f"{client['name']}_{server['name']}.conf"
    return send_file(temp_path, as_attachment=True, download_name=filename)

@app.route('/api/clients', methods=['GET'])
def get_all_clients():
    clients = amnezia_manager.get_client_configs()
    return jsonify(clients)

@app.route('/api/system/status')
def system_status():
    status = {
        "awg_available": os.path.exists("/usr/bin/awg") and os.path.exists("/usr/bin/awg-quick"),
        "public_ip": amnezia_manager.public_ip,
        "total_servers": len(amnezia_manager.config["servers"]),
        "total_clients": len(amnezia_manager.config["clients"]),
        "active_servers": len([s for s in amnezia_manager.config["servers"]
                             if amnezia_manager.get_server_status(s["id"]) == "running"]),
        "timestamp": time.time(),
        "environment": {
            "nginx_port": NGINX_PORT,
            "auto_start_servers": AUTO_START_SERVERS,
            "default_mtu": DEFAULT_MTU,
            "default_subnet": DEFAULT_SUBNET,
            "default_port": DEFAULT_PORT,
            "default_dns": DEFAULT_DNS
        }
    }
    return jsonify(status)

@app.route('/api/system/refresh-ip')
def refresh_ip():
    """Refresh public IP address"""
    new_ip = amnezia_manager.detect_public_ip()
    amnezia_manager.public_ip = new_ip

    # Update all servers with new IP
    for server in amnezia_manager.config["servers"]:
        server["public_ip"] = new_ip

    amnezia_manager.save_config()
    return jsonify({"public_ip": new_ip})

@app.route('/api/servers/<server_id>/config')
def get_server_config(server_id):
    """Get the raw WireGuard server configuration"""
    server = next((s for s in amnezia_manager.config['servers'] if s['id'] == server_id), None)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    try:
        # Read the actual config file
        if os.path.exists(server['config_path']):
            with open(server['config_path'], 'r') as f:
                config_content = f.read()

            return jsonify({
                "server_id": server_id,
                "server_name": server['name'],
                "config_path": server['config_path'],
                "config_content": config_content,
                "interface": server['interface'],
                "public_key": server['server_public_key']
            })
        else:
            return jsonify({"error": "Config file not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to read config: {str(e)}"}), 500

@app.route('/api/servers/<server_id>/config/download')
def download_server_config(server_id):
    """Download the WireGuard server configuration file"""
    server = next((s for s in amnezia_manager.config['servers'] if s['id'] == server_id), None)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    try:
        if os.path.exists(server['config_path']):
            return send_file(
                server['config_path'],
                as_attachment=True,
                download_name=f"{server['interface']}.conf"
            )
        else:
            return jsonify({"error": "Config file not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to download config: {str(e)}"}), 500

@app.route('/api/servers/<server_id>/info')
def get_server_info(server_id):
    """Get detailed server information including config preview and default I values"""
    server = next((s for s in amnezia_manager.config['servers'] if s['id'] == server_id), None)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    # Get current status
    current_status = amnezia_manager.get_server_status(server_id)
    server['current_status'] = current_status

    # Try to read config file for preview
    config_preview = ""
    if os.path.exists(server['config_path']):
        try:
            with open(server['config_path'], 'r') as f:
                lines = f.readlines()
                config_preview = ''.join(lines[:min(10, len(lines))])
        except:
            config_preview = "Unable to read config file"

    server_info = {
        "id": server['id'],
        "name": server['name'],
        "protocol": server['protocol'],
        "port": server['port'],
        "status": current_status,
        "interface": server['interface'],
        "config_path": server['config_path'],
        "public_ip": server['public_ip'],
        "server_ip": server['server_ip'],
        "subnet": server['subnet'],
        "mtu": server.get('mtu', 1420),
        "obfuscation_enabled": server['obfuscation_enabled'],
        "obfuscation_params": server.get('obfuscation_params', {}),
        "clients_count": len(server['clients']),
        "created_at": server['created_at'],
        "config_preview": config_preview,
        "public_key": server['server_public_key'],
        "dns": server['dns'],
        "default_i_settings": {
            "i1": DEFAULT_I1,
            "i2": DEFAULT_I2,
            "i3": DEFAULT_I3,
            "i4": DEFAULT_I4,
            "i5": DEFAULT_I5
        }
    }

    return jsonify(server_info)

@app.route('/api/default-i-settings', methods=['GET'])
def get_default_i_settings():
    return jsonify({
        "i1": DEFAULT_I1,
        "i2": DEFAULT_I2,
        "i3": DEFAULT_I3,
        "i4": DEFAULT_I4,
        "i5": DEFAULT_I5
    })

@app.route('/api/servers', methods=['GET'])
def get_servers():
    # Update server status based on actual interface state
    for server in amnezia_manager.config["servers"]:
        server["status"] = amnezia_manager.get_server_status(server["id"])
        # Ensure MTU is included in basic server list
        if 'mtu' not in server:
            server['mtu'] = 1420  # Default value

    amnezia_manager.save_config()
    return jsonify(amnezia_manager.config["servers"])

@app.route('/api/system/iptables-test')
def iptables_test():
    """Test iptables setup for a specific server"""
    server_id = request.args.get('server_id')
    if not server_id:
        return jsonify({"error": "server_id parameter required"}), 400

    server = next((s for s in amnezia_manager.config['servers'] if s['id'] == server_id), None)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    # Test iptables rules
    try:
        # Check if rules exist
        check_commands = [
            f"iptables -L INPUT -n | grep {server['interface']}",
            f"iptables -L FORWARD -n | grep {server['interface']}",
            f"iptables -t nat -L POSTROUTING -n | grep {server['subnet']}"
        ]

        results = {}
        for cmd in check_commands:
            try:
                result = amnezia_manager.execute_command(cmd)
                results[cmd] = "Found" if result else "Not found"
            except:
                results[cmd] = "Error"

        return jsonify({
            "server_id": server_id,
            "server_name": server['name'],
            "interface": server['interface'],
            "subnet": server['subnet'],
            "iptables_check": results
        })

    except Exception as e:
        return jsonify({"error": f"iptables test failed: {str(e)}"}), 500
    
@app.route('/api/servers/<server_id>/clients/<client_id>/config-both')
def get_client_config_both(server_id, client_id):
    """Get both clean and full client configurations"""
    client = amnezia_manager.config["clients"].get(client_id)
    if not client or client.get("server_id") != server_id:
        return jsonify({"error": "Client not found"}), 404

    server = next((s for s in amnezia_manager.config['servers'] if s['id'] == server_id), None)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    # Generate both versions
    clean_config = amnezia_manager.generate_wireguard_client_config(
        server, client, include_comments=False
    )
    
    full_config = amnezia_manager.generate_wireguard_client_config(
        server, client, include_comments=True
    )
    
    return jsonify({
        "server_id": server_id,
        "client_id": client_id,
        "client_name": client['name'],
        "clean_config": clean_config,
        "full_config": full_config,
        "clean_length": len(clean_config),
        "full_length": len(full_config),
        "created_at": client['created_at'],
        "created_at_readable": time.ctime(client.get('created_at')) if client.get('created_at') else None,
        "suspend_at": client.get('suspend_at'),
        "suspend_at_readable": time.ctime(client.get('suspend_at')) if client.get('suspend_at') else None
    })
    
@app.route('/api/servers/<server_id>/clients/<client_id>/suspend', methods=['POST'])
def suspend_client(server_id, client_id):
    """Suspend a client"""
    success, message = amnezia_manager.suspend_client(server_id, client_id)
    if success:
        return jsonify({"status": "suspended", "client_id": client_id, "message": message})
    return jsonify({"error": message}), 404

@app.route('/api/servers/<server_id>/clients/<client_id>/activate', methods=['POST'])
def activate_client(server_id, client_id):
    """Activate a suspended client"""
    success, message = amnezia_manager.activate_client(server_id, client_id)
    if success:
        return jsonify({"status": "activated", "client_id": client_id, "message": message})
    return jsonify({"error": message}), 404

@app.route('/api/servers/<server_id>/clients/<client_id>/suspend-time', methods=['PUT'])
def update_client_suspend_time(server_id, client_id):
    """Update client scheduled suspension time"""
    data = request.json
    suspend_at = data.get('suspend_at')
    
    # Convert ISO datetime string to timestamp if provided
    if suspend_at:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(suspend_at.replace('Z', '+00:00'))
            suspend_at = dt.timestamp()
        except:
            return jsonify({"error": "Invalid datetime format"}), 400
    
    client, message = amnezia_manager.update_client_suspend_time(server_id, client_id, suspend_at)
    if client:
        return jsonify({
            "client": client,
            "message": message
        })
    return jsonify({"error": message}), 404
    
@app.route('/api/servers/<server_id>/traffic')
def get_server_traffic(server_id):
    traffic = amnezia_manager.get_peer_traffic_for_server(server_id)
    if traffic is None:
        return jsonify({"error": "Server not found or no traffic data"}), 404
    return jsonify(traffic)

@app.route('/api/servers/traffic')
def get_all_servers_traffic():
    """Get interface traffic for all servers"""
    traffic = amnezia_manager.get_all_servers_traffic()
    return jsonify(traffic)

@app.route('/status')
def get_container_uptime():
    # Get the modification time of /proc/1/cmdline (container start time epoch)
    result = subprocess.check_output(["stat", "-c %Y", "/proc/1/cmdline"], text=True)
    uptime_seconds_epoch = int(result.strip())

    now_epoch = int(time.time())
    
    uptime_seconds = now_epoch - uptime_seconds_epoch
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    return f"Container Uptime: {days}d {hours}h {minutes}m {seconds}s"

@app.route('/api/logs/list')
def get_logs_list():
    """Get list of available log files"""
    # Check which files exist
    available_logs = []
    for log in ALLOWED_LOG_FILES:
        if os.path.exists(log["path"]):
            stat = os.stat(log["path"])
            available_logs.append({
                "name": log["name"],
                "path": log["path"],
                "type": log["type"],
                "size": stat.st_size,
                "size_human": format_bytes(stat.st_size)
            })
    
    return jsonify(available_logs)

@app.route('/api/logs/view')
def view_log():
    """Get last N lines of a log file"""
    requested_path = request.args.get('path')
    requested_type = request.args.get('type')
    lines = request.args.get('lines', 100, type=int)

    log_path = None
    if requested_type and requested_type in ALLOWED_LOG_TYPES:
        log_path = ALLOWED_LOG_TYPES[requested_type]
    elif requested_path and requested_path in ALLOWED_LOG_PATHS:
        log_path = requested_path

    if not log_path:
        return jsonify({"error": "Invalid log selection"}), 400
    
    if not os.path.exists(log_path):
        return jsonify({"error": "Log file not found"}), 404
    
    try:
        # Use tail command to get last N lines
        result = subprocess.run(
            ["tail", "-n", str(lines), log_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        return jsonify({
            "path": log_path,
            "lines": result.stdout,
            "line_count": len(result.stdout.splitlines()),
            "total_lines": int(subprocess.run(
                ["wc", "-l", log_path],
                capture_output=True,
                text=True,
                check=True
            ).stdout.split()[0])
        })
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to read log: {str(e)}"}), 500

@app.route('/api/logs/download')
def download_log():
    """Download complete log file"""
    requested_type = request.args.get('type')

    log_path = None
    if requested_type and requested_type in ALLOWED_LOG_TYPES:
        log_path = ALLOWED_LOG_TYPES[requested_type]

    safe_log_path = resolve_allowed_log_path(log_path)
    if not safe_log_path:
        return jsonify({"error": "Invalid log selection"}), 400
    
    if not os.path.exists(safe_log_path):
        return jsonify({"error": "Log file not found"}), 404
    
    # Get filename from path
    filename = os.path.basename(safe_log_path)
    safe_log_dir = os.path.dirname(safe_log_path)
    
    return send_from_directory(
        directory=safe_log_dir,
        path=filename,
        as_attachment=True,
        download_name=f"{filename}",
        mimetype="text/plain"
    )

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

@socketio.on('connect')
def handle_connect():
    print(f"WebSocket connected from {request.remote_addr}")
    
    socketio.emit('status', {
        'message': 'Connected to AmneziaWG Web UI',
        'public_ip': amnezia_manager.public_ip,
        'nginx_port': NGINX_PORT,
        'server_port': request.environ.get('SERVER_PORT', 'unknown'),
        'client_port': request.environ.get('HTTP_X_FORWARDED_PORT', 'unknown')
    })
    
    all_client_traffic = {}
    for server in amnezia_manager.config['servers']:
        server_id = server['id']
        traffic = amnezia_manager.get_peer_traffic_for_server(server_id)
        if traffic:
            all_client_traffic[server_id] = traffic
    
    server_interface_traffic = amnezia_manager.get_all_servers_traffic()
    
    if all_client_traffic or server_interface_traffic:
        socketio.emit('traffic_update', {
            'timestamp': time.time(),
            'client_traffic': all_client_traffic,
            'server_traffic': server_interface_traffic
        })

@socketio.on('disconnect')
def handle_disconnect():
    print(f"WebSocket disconnected from {request.remote_addr}")

if __name__ == '__main__':
    print(f"AmneziaWG Web UI starting...")
    print(f"Configuration:")
    print(f"  NGINX Port: {NGINX_PORT}")
    print(f"  Auto-start: {AUTO_START_SERVERS}")
    print(f"  Default MTU: {DEFAULT_MTU}")
    print(f"  Default Subnet: {DEFAULT_SUBNET}")
    print(f"  Default Port: {DEFAULT_PORT}")
    print(f"Detected public IP: {amnezia_manager.public_ip}")

    if AUTO_START_SERVERS:
        print("Auto-starting existing servers...")

    socketio.run(app, host='0.0.0.0', port=WEB_UI_PORT, debug=False, allow_unsafe_werkzeug=True)