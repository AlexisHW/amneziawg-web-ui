// AmneziaWG Web UI - Main Application JavaScript
class AmneziaApp {
    constructor() {
        this.socket = null;
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            console.log("AmneziaWG Web UI initializing...");
            this.setupEventListeners();
            this.setupSocketIO();
            this.loadInitialData();
        });
    }

    // Utility function to safely get elements
    getElement(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with id '${id}' not found`);
        }
        return element;
    }

    setupEventListeners() {
        // Server form submission
        const serverForm = this.getElement('serverForm');
        if (serverForm) {
            serverForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createServer();
            });
        }

        // Test create button
        const testCreateBtn = this.getElement('testCreateBtn');
        if (testCreateBtn) {
            testCreateBtn.addEventListener('click', () => {
                this.testCreateServer();
            });
        }

        // Random parameters button
        const randomParamsBtn = this.getElement('randomParamsBtn');
        if (randomParamsBtn) {
            randomParamsBtn.addEventListener('click', () => {
                this.generateRandomParams();
            });
        }

        // Refresh IP button
        const refreshIpBtn = this.getElement('refreshIpBtn');
        if (refreshIpBtn) {
            refreshIpBtn.addEventListener('click', () => {
                this.refreshPublicIp();
            });
        }

        // Obfuscation toggle
        const obfuscationCheckbox = this.getElement('enableObfuscation');
        if (obfuscationCheckbox) {
            obfuscationCheckbox.addEventListener('change', (e) => {
                this.toggleObfuscationParams(e.target.checked);
            });
            // Initialize visibility
            this.toggleObfuscationParams(obfuscationCheckbox.checked);
        }

        // Form validation listeners
        this.setupFormValidation();
    }

    setupFormValidation() {
        const nameElement = this.getElement('serverName');
        const portElement = this.getElement('serverPort');
        const subnetElement = this.getElement('serverSubnet');
        
        if (nameElement) {
            nameElement.addEventListener('input', () => {
                this.hideError('nameError');
            });
        }
        
        if (portElement) {
            portElement.addEventListener('input', () => {
                this.hideError('portError');
            });
        }
        
        if (subnetElement) {
            subnetElement.addEventListener('input', () => {
                this.hideError('subnetError');
            });
        }
    }

    hideError(errorId) {
        const errorElement = this.getElement(errorId);
        if (errorElement) {
            errorElement.classList.add('hidden');
        }
    }

    toggleObfuscationParams(show) {
        const obfuscationParams = this.getElement('obfuscationParams');
        if (obfuscationParams) {
            obfuscationParams.style.display = show ? 'block' : 'none';
        }
    }

    setupSocketIO() {
        // Get the current host and protocol
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port;

        let socketUrl;
        if (port && port !== '' && port !== '80' && port !== '443') {
            socketUrl = `${protocol}//${hostname}:${port}`;
        } else {
            socketUrl = `${protocol}//${hostname}`;
        }

        this.socket = io(socketUrl, {
            path: '/socket.io',
            transports: ['websocket', 'polling'] // Explicitly set transports
        });

        this.socket.on('connect', () => {
            console.log("✅ Connected to server via WebSocket");
            this.updateStatus('Connected to AmneziaWG Web UI');
        });

        this.socket.on('disconnect', () => {
            console.log("❌ Disconnected from server:", reason);
            this.updateStatus('Disconnected from AmneziaWG Web UI');
        });

        this.socket.on('connect_error', (error) => {
            console.error("❌ WebSocket connection error:", error);
            this.updateStatus('Connection error - retrying...');
        });

        this.socket.on('status', (data) => {
            console.log("Status update:", data);
            if (data.public_ip) {
                this.updatePublicIp(data.public_ip);
            }
        });

        this.socket.on('server_status', (data) => {
            console.log("Server status update:", data);
            this.loadServers();
        });
    }

    updateStatus(message) {
        const statusElement = this.getElement('status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }

    updatePublicIp(ip) {
        const publicIpElement = this.getElement('publicIp');
        if (publicIpElement) {
            publicIpElement.textContent = ip;
        }
    }

    refreshPublicIp() {
        fetch('/api/system/refresh-ip')
            .then(response => response.json())
            .then(data => {
                this.updatePublicIp(data.public_ip);
                this.loadServers();
            })
            .catch(error => {
                console.error('Error refreshing IP:', error);
            });
    }

    generateRandomParams() {
        // Generate random values within recommended ranges
        const jcElement = this.getElement('paramJc');
        const s1Element = this.getElement('paramS1');
        const s2Element = this.getElement('paramS2');
        const h1Element = this.getElement('paramH1');
        const h2Element = this.getElement('paramH2');
        const h3Element = this.getElement('paramH3');
        const h4Element = this.getElement('paramH4');
        
        if (jcElement) jcElement.value = Math.floor(Math.random() * 9) + 4; // 4-12
        if (s1Element) s1Element.value = Math.floor(Math.random() * 136) + 15; // 15-150
        if (s2Element) s2Element.value = Math.floor(Math.random() * 136) + 15; // 15-150
        
        // Generate unique H values
        const hValues = new Set();
        while (hValues.size < 4) {
            hValues.add(Math.floor(Math.random() * 1000000) + 1000);
        }
        const hArray = Array.from(hValues);
        
        if (h1Element) h1Element.value = hArray[0];
        if (h2Element) h2Element.value = hArray[1];
        if (h3Element) h3Element.value = hArray[2];
        if (h4Element) h4Element.value = hArray[3];
    }

    showFormStatus(message, type) {
        const statusDiv = this.getElement('formStatus');
        if (statusDiv) {
            statusDiv.textContent = message;
            statusDiv.className = `text-sm mt-2 ${type === 'success' ? 'text-green-600' : 'text-red-600'}`;
            statusDiv.classList.remove('hidden');
            
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    }

    validateForm() {
        let isValid = true;

        // Reset errors
        this.hideError('nameError');
        this.hideError('portError');
        this.hideError('subnetError');
        this.hideError('mtuError');
        this.hideError('dnsError'); // New DNS error

        // Validate name
        const nameElement = this.getElement('serverName');
        const name = nameElement ? nameElement.value.trim() : '';
        if (!name) {
            this.showError('nameError', 'Server name is required');
            isValid = false;
        }

        // Validate port
        const portElement = this.getElement('serverPort');
        const port = portElement ? parseInt(portElement.value) : 0;
        if (!port || port < 1 || port > 65535) {
            this.showError('portError', 'Port must be between 1 and 65535');
            isValid = false;
        }

        // Validate subnet
        const subnetElement = this.getElement('serverSubnet');
        const subnet = subnetElement ? subnetElement.value : '';
        const subnetRegex = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
        if (!subnet || !subnetRegex.test(subnet)) {
            this.showError('subnetError', 'Valid subnet is required (e.g., 10.0.0.0/24)');
            isValid = false;
        }

        // Validate MTU
        const mtuElement = this.getElement('serverMTU');
        const mtu = mtuElement ? parseInt(mtuElement.value) : 0;
        if (!mtu || mtu < 1280 || mtu > 1440) {
            this.showError('mtuError', 'MTU must be between 1280 and 1440');
            isValid = false;
        }

        // Validate DNS
        const dnsElement = this.getElement('serverDNS');
        const dns = dnsElement ? dnsElement.value.trim() : '';
        const dnsServers = dns.split(',').map(s => s.trim()).filter(s => s);
        const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;

        if (!dns || dnsServers.length === 0) {
            this.showError('dnsError', 'At least one DNS server is required');
            isValid = false;
        } else {
            for (const dnsServer of dnsServers) {
                if (!ipRegex.test(dnsServer)) {
                    this.showError('dnsError', `Invalid DNS server IP: ${dnsServer}`);
                    isValid = false;
                    break;
                }
            }
        }

        return isValid;
    }

    // Add DNS input validation listener
    setupFormValidation() {
        const nameElement = this.getElement('serverName');
        const portElement = this.getElement('serverPort');
        const subnetElement = this.getElement('serverSubnet');
        const mtuElement = this.getElement('serverMTU');
        const dnsElement = this.getElement('serverDNS'); // New DNS element

        if (nameElement) {
            nameElement.addEventListener('input', () => {
                this.hideError('nameError');
            });
        }

        if (portElement) {
            portElement.addEventListener('input', () => {
                this.hideError('portError');
            });
        }

        if (subnetElement) {
            subnetElement.addEventListener('input', () => {
                this.hideError('subnetError');
            });
        }

        if (mtuElement) {
            mtuElement.addEventListener('input', () => {
                this.hideError('mtuError');
            });
        }

        if (dnsElement) {
            dnsElement.addEventListener('input', () => {
                this.hideError('dnsError');
            });
        }
    }

    showError(errorId, message) {
        const errorElement = this.getElement(errorId);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
    }

    createServer() {
        console.log("Creating server...");

        if (!this.validateForm()) {
            console.log("Form validation failed");
            this.showFormStatus('Please fix the form errors above', 'error');
            return;
        }

        // Safely get form values with fallbacks
        const nameElement = this.getElement('serverName');
        const portElement = this.getElement('serverPort');
        const subnetElement = this.getElement('serverSubnet');
        const mtuElement = this.getElement('serverMTU');
        const dnsElement = this.getElement('serverDNS'); // New DNS element
        const obfuscationElement = this.getElement('enableObfuscation');
        const autoStartElement = this.getElement('autoStart');

        const formData = {
            name: nameElement ? nameElement.value.trim() : 'New Server',
            port: portElement ? parseInt(portElement.value) : 51820,
            subnet: subnetElement ? subnetElement.value : '10.0.0.0/24',
            mtu: mtuElement ? parseInt(mtuElement.value) : 1280,
            dns: dnsElement ? dnsElement.value.trim() : '8.8.8.8,1.1.1.1', // New DNS field
            obfuscation: obfuscationElement ? obfuscationElement.checked : true,
            auto_start: autoStartElement ? autoStartElement.checked : true
        };

        console.log("Form data:", formData);

        // Add obfuscation parameters if enabled
        if (formData.obfuscation) {
            formData.obfuscation_params = {
                Jc: parseInt(this.getElement('paramJc')?.value || '8'),
                Jmin: parseInt(this.getElement('paramJmin')?.value || '8'),
                Jmax: parseInt(this.getElement('paramJmax')?.value || '80'),
                S1: parseInt(this.getElement('paramS1')?.value || '50'),
                S2: parseInt(this.getElement('paramS2')?.value || '60'),
                H1: parseInt(this.getElement('paramH1')?.value || '1000'),
                H2: parseInt(this.getElement('paramH2')?.value || '2000'),
                H3: parseInt(this.getElement('paramH3')?.value || '3000'),
                H4: parseInt(this.getElement('paramH4')?.value || '4000'),
                MTU: formData.mtu
            };
        }

        // Disable button and show loading
        this.setCreateButtonState(true);

        fetch('/api/servers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                },
            body: JSON.stringify(formData)
        })
        .then(response => {
            console.log("Response received:", response.status);
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || `HTTP ${response.status}`);
                });
            }
            return response.json();
        })
        .then(server => {
            console.log("Server created successfully:", server);
            this.showFormStatus(`Server "${server.name}" created successfully!`, 'success');

            // Reset form
            const serverForm = this.getElement('serverForm');
            if (serverForm) serverForm.reset();

            this.loadServers();
        })
        .catch(error => {
            console.error('Error creating server:', error);
            this.showFormStatus('Error creating server: ' + error.message, 'error');
        })
        .finally(() => {
            // Re-enable button
            this.setCreateButtonState(false);
        });
    }

    setCreateButtonState(loading) {
        const createButton = this.getElement('createButton');
        if (createButton) {
            createButton.disabled = loading;
            createButton.textContent = loading ? 'Creating...' : 'Create Server';
            createButton.classList.toggle('opacity-50', loading);
        }
    }

    testCreateServer() {
        console.log("Test button clicked");
        
        const testData = {
            name: "Test Server " + Date.now(),
            port: 51820,
            subnet: "10.0.0.0/24",
            obfuscation: true,
            auto_start: true
        };
        
        console.log("Sending test data:", testData);
        
        fetch('/api/servers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testData)
        })
        .then(response => {
            console.log("Response status:", response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(server => {
            console.log("Server created successfully:", server);
            this.showFormStatus('Test server created successfully!', 'success');
            this.loadServers();
        })
        .catch(error => {
            console.error('Error creating server:', error);
            this.showFormStatus('Error creating server: ' + error.message, 'error');
        });
    }

    loadInitialData() {
        this.loadServers();
        this.loadPublicIp();
    }

    loadPublicIp() {
        fetch('/api/system/status')
            .then(response => response.json())
            .then(data => {
                this.updatePublicIp(data.public_ip);
            })
            .catch(error => {
                console.error('Error loading public IP:', error);
            });
    }

    loadServers() {
        fetch('/api/servers')
            .then(response => response.json())
            .then(servers => {
                this.renderServers(servers);
            })
            .catch(error => {
                console.error('Error loading servers:', error);
                this.showServerError('Failed to load servers');
            });
    }

    renderServers(servers) {
        const serversList = this.getElement('serversList');
        if (!serversList) return;

        if (servers.length === 0) {
            serversList.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    No servers created yet. Create your first server above.
                </div>
            `;
            return;
        }

        serversList.innerHTML = servers.map(server => `
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h3 class="text-lg font-semibold">${server.name}</h3>
                        <p class="text-sm text-gray-600">
                            ID: ${server.id} | Port: ${server.port} | Subnet: ${server.subnet}
                            ${server.obfuscation_enabled ? '| 🔒 Obfuscated' : ''}
                        </p>
                        <p class="text-sm text-gray-500">Public IP: ${server.public_ip}</p>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="px-3 py-1 rounded-full text-sm ${
                            server.status === 'running' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }">${server.status}</span>
                        <button onclick="amneziaApp.deleteServer('${server.id}')" class="text-red-500 hover:text-red-700">
                            🗑️ Delete
                        </button>
                    </div>
                </div>
                <div class="space-x-2 mb-4">
                    <button onclick="amneziaApp.startServer('${server.id}')" class="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600">
                        Start
                    </button>
                    <button onclick="amneziaApp.stopServer('${server.id}')" class="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600">
                        Stop
                    </button>
                    <button onclick="amneziaApp.addClient('${server.id}')" class="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
                        Add Client
                    </button>
                    <button onclick="amneziaApp.showServerConfig('${server.id}')" class="bg-purple-500 text-white px-3 py-1 rounded hover:bg-purple-600">
                        Show Config
                    </button>
                </div>
                <div id="clients-${server.id}">
                    ${this.renderServerClients(server.id, server.clients || [])}
                </div>
            </div>
        `).join('');

        // Load clients for each server
        servers.forEach(server => {
            this.loadServerClients(server.id);
        });
    }

    renderServerClients(serverId, clients) {
        if (clients.length === 0) {
            return '<p class="text-gray-500 text-sm">No clients yet.</p>';
        }
        
        return `
            <h4 class="font-medium mb-2">Clients (${clients.length}):</h4>
            <div class="space-y-2">
                ${clients.map(client => `
                    <div class="flex justify-between items-center bg-gray-50 p-3 rounded-lg hover:bg-gray-100 transition-colors duration-200">
                        <div class="flex items-center">
                            <div class="w-8 h-8 flex items-center justify-center bg-blue-100 text-blue-600 rounded-full mr-3">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                                </svg>
                            </div>
                            <div>
                                <span class="font-medium">${client.name}</span>
                                <span class="text-sm text-gray-600 ml-2">${client.client_ip}</span>
                            </div>
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="amneziaApp.showClientQRCode('${serverId}', '${client.id}', '${client.name}')"
                                    class="bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 shadow hover:shadow-md flex items-center"
                                    title="Show QR Code">
                                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"/>
                                </svg>
                                QR Code
                            </button>
                            <button onclick="amneziaApp.downloadClientConfig('${serverId}', '${client.id}')"
                                    class="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 shadow hover:shadow-md flex items-center">
                                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                                Download
                            </button>
                            <button onclick="amneziaApp.deleteClient('${serverId}', '${client.id}')"
                                    class="bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 shadow hover:shadow-md flex items-center">
                                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                                Delete
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    loadServerClients(serverId) {
        fetch(`/api/servers/${serverId}/clients`)
            .then(response => response.json())
            .then(clients => {
                const clientsContainer = this.getElement(`clients-${serverId}`);
                if (clientsContainer) {
                    clientsContainer.innerHTML = this.renderServerClients(serverId, clients);
                }
            })
            .catch(error => {
                console.error(`Error loading clients for server ${serverId}:`, error);
            });
    }

    showServerError(message) {
        const serversList = this.getElement('serversList');
        if (serversList) {
            serversList.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    ${message}
                </div>
            `;
        }
    }

    // Server management methods
    deleteServer(serverId) {
        if (confirm('Are you sure you want to delete this server and all its clients?')) {
            fetch(`/api/servers/${serverId}`, { method: 'DELETE' })
                .then(() => this.loadServers())
                .catch(error => {
                    console.error('Error deleting server:', error);
                    alert('Error deleting server: ' + error.message);
                });
        }
    }

    deleteClient(serverId, clientId) {
        if (confirm('Are you sure you want to delete this client?')) {
            fetch(`/api/servers/${serverId}/clients/${clientId}`, { method: 'DELETE' })
                .then(() => this.loadServers())
                .catch(error => {
                    console.error('Error deleting client:', error);
                    alert('Error deleting client: ' + error.message);
                });
        }
    }

    startServer(serverId) {
        fetch(`/api/servers/${serverId}/start`, { method: 'POST' })
            .then(() => this.loadServers())
            .catch(error => {
                console.error('Error starting server:', error);
                alert('Error starting server: ' + error.message);
            });
    }

    stopServer(serverId) {
        fetch(`/api/servers/${serverId}/stop`, { method: 'POST' })
            .then(() => this.loadServers())
            .catch(error => {
                console.error('Error stopping server:', error);
                alert('Error stopping server: ' + error.message);
            });
    }

    addClient(serverId) {
        const clientName = prompt('Enter client name:');
        if (clientName) {
            fetch(`/api/servers/${serverId}/clients`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: clientName })
            })
            .then(() => this.loadServers())
            .catch(error => {
                console.error('Error adding client:', error);
                alert('Error adding client: ' + error.message);
            });
        }
    }

    downloadClientConfig(serverId, clientId) {
        window.open(`/api/servers/${serverId}/clients/${clientId}/config`, '_blank');
    }

    showServerConfig(serverId) {
        fetch(`/api/servers/${serverId}/info`)
            .then(response => response.json())
            .then(serverInfo => {
                this.displayServerConfigModal(serverInfo);
            })
            .catch(error => {
                console.error('Error fetching server info:', error);
                alert('Error loading server configuration: ' + error.message);
            });
    }

    showRawServerConfig(serverId) {
        fetch(`/api/servers/${serverId}/config`)
            .then(response => response.json())
            .then(config => {
                this.displayRawConfigModal(config);
            })
            .catch(error => {
                console.error('Error fetching server config:', error);
                alert('Error loading server configuration: ' + error.message);
            });
    }

    downloadServerConfig(serverId) {
        window.open(`/api/servers/${serverId}/config/download`, '_blank');
    }

    displayServerConfigModal(serverInfo) {
        const modalHtml = `
            <div id="configModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
                    <div class="mt-3">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-medium text-gray-900">Server Configuration: ${serverInfo.name}</h3>
                            <button onclick="amneziaApp.closeModal()" class="text-gray-400 hover:text-gray-600">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <div class="bg-gray-50 p-3 rounded">
                                <h4 class="font-semibold text-sm text-gray-700 mb-2">Basic Information</h4>
                                <div class="space-y-1 text-sm">
                                    <div><span class="font-medium">Interface:</span> ${serverInfo.interface}</div>
                                    <div><span class="font-medium">Port:</span> ${serverInfo.port}</div>
                                    <div><span class="font-medium">Subnet:</span> ${serverInfo.subnet}</div>
                                    <div><span class="font-medium">Server IP:</span> ${serverInfo.server_ip}</div>
                                    <div><span class="font-medium">Public IP:</span> ${serverInfo.public_ip}</div>
                                    <div><span class="font-medium">Status:</span>
                                        <span class="px-2 py-1 rounded-full text-xs ${
                                            serverInfo.status === 'running' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                        }">${serverInfo.status}</span>
                                    </div>
                                </div>
                            </div>

                            <div class="bg-gray-50 p-3 rounded">
                                <h4 class="font-semibold text-sm text-gray-700 mb-2">Configuration</h4>
                                <div class="space-y-1 text-sm">
                                    <div><span class="font-medium">Protocol:</span> ${serverInfo.protocol}</div>
                                    <div><span class="font-medium">Obfuscation:</span> ${serverInfo.obfuscation_enabled ? 'Enabled' : 'Disabled'}</div>
                                    <div><span class="font-medium">Clients:</span> ${serverInfo.clients_count}</div>
                                    <div><span class="font-medium">DNS:</span> ${serverInfo.dns.join(', ')}</div>
                                    <div><span class="font-medium">MTU:</span> ${serverInfo.mtu}</div>
                                    <div class="truncate"><span class="font-medium">Public Key:</span>
                                        <span class="font-mono text-xs">${serverInfo.public_key}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        ${serverInfo.obfuscation_enabled ? `
                        <div class="bg-blue-50 p-3 rounded mb-4">
                            <h4 class="font-semibold text-sm text-blue-700 mb-2">Obfuscation Parameters</h4>
                            <div class="grid grid-cols-3 md:grid-cols-6 gap-2 text-xs">
                                ${Object.entries(serverInfo.obfuscation_params).map(([key, value]) => `
                                    <div class="text-center">
                                        <div class="font-medium">${key}</div>
                                        <div class="font-mono">${value}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        ` : ''}

                        <div class="mb-4">
                            <h4 class="font-semibold text-sm text-gray-700 mb-2">Configuration Preview</h4>
                            <pre class="bg-gray-800 text-green-400 p-3 rounded text-xs overflow-x-auto max-h-40 overflow-y-auto">${serverInfo.config_preview}</pre>
                        </div>

                        <div class="flex justify-end space-x-3 pt-4 border-t">
                            <button onclick="amneziaApp.showRawServerConfig('${serverInfo.id}')"
                                    class="bg-blue-500 text-white px-4 py-2 rounded text-sm hover:bg-blue-600">
                                View Full Config
                            </button>
                            <button onclick="amneziaApp.downloadServerConfig('${serverInfo.id}')"
                                    class="bg-green-500 text-white px-4 py-2 rounded text-sm hover:bg-green-600">
                                Download Config
                            </button>
                            <button onclick="amneziaApp.closeModal()"
                                    class="bg-gray-500 text-white px-4 py-2 rounded text-sm hover:bg-gray-600">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    displayRawConfigModal(config) {
        const modalHtml = `
            <div id="rawConfigModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                <div class="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
                    <div class="mt-3">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-medium text-gray-900">Raw Configuration: ${config.server_name}</h3>
                            <button onclick="amneziaApp.closeModal()" class="text-gray-400 hover:text-gray-600">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>

                        <div class="mb-4">
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-sm text-gray-600">Config path: ${config.config_path}</span>
                                <button onclick="amneziaApp.copyToClipboard('${btoa(JSON.stringify(config))}')"
                                        class="bg-gray-500 text-white px-3 py-1 rounded text-xs hover:bg-gray-600">
                                    Copy JSON
                                </button>
                            </div>
                            <pre class="bg-gray-900 text-green-400 p-4 rounded text-sm overflow-x-auto max-h-96 overflow-y-auto">${config.config_content}</pre>
                        </div>

                        <div class="flex justify-end space-x-3 pt-4 border-t">
                            <button onclick="amneziaApp.downloadServerConfig('${config.server_id}')"
                                    class="bg-green-500 text-white px-4 py-2 rounded text-sm hover:bg-green-600">
                                Download Config
                            </button>
                            <button onclick="amneziaApp.closeModal()"
                                    class="bg-gray-500 text-white px-4 py-2 rounded text-sm hover:bg-gray-600">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Close any existing modal first
        this.closeModal();
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    closeModal() {
        const existingModal = document.getElementById('configModal') || document.getElementById('rawConfigModal');
        if (existingModal) {
            existingModal.remove();
        }
    }

    showClientQRCode(serverId, clientId, clientName) {
        // Create modal for QR code
        const modalHtml = `
            <div id="qrModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
                <div class="relative p-8 border w-11/12 md:w-3/4 lg:w-2/3 xl:w-1/2 shadow-2xl rounded-2xl bg-white">
                    <div class="flex flex-col">
                        <div class="flex justify-between items-center w-full mb-6">
                            <h3 class="text-xl font-bold text-gray-900">QR Code for ${clientName}</h3>
                            <button onclick="amneziaApp.closeQRModal()"
                                    class="text-gray-400 hover:text-gray-600 transition-colors duration-200 p-1 rounded-full hover:bg-gray-100">
                                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>
                        
                        <div class="flex flex-col lg:flex-row gap-8 mb-6">
                            <!-- Left side: QR Code -->
                            <div class="lg:w-2/5">
                                <div class="bg-white p-6 rounded-xl border-2 border-gray-100 shadow-inner">
                                    <div id="qrcode" class="flex justify-center mb-4"></div>
                                    <p class="text-center text-sm text-gray-500">Scan with WireGuard app</p>
                                </div>
                                <!-- Download QR Code button outside the box -->
                                <div class="mt-4 text-center">
                                    <button onclick="amneziaApp.downloadQRCode()"
                                            class="inline-flex items-center bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 shadow hover:shadow-lg transform hover:-translate-y-0.5">
                                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                                        </svg>
                                        Download QR Code Image
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Right side: Configuration Text -->
                            <div class="lg:w-3/5">
                                <div class="mb-4">
                                    <div class="flex items-center justify-between mb-2">
                                        <label class="block text-sm font-medium text-gray-700">Configuration Text</label>
                                        <div class="flex space-x-2">
                                            <button onclick="amneziaApp.toggleConfigView()"
                                                    class="text-blue-500 hover:text-blue-700 text-sm font-medium px-3 py-1.5 rounded-lg border border-blue-200 hover:bg-blue-50 transition-colors duration-200">
                                                Toggle View
                                            </button>
                                            <button onclick="amneziaApp.copyConfigText()"
                                                    class="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors duration-200 shadow hover:shadow-md">
                                                Copy Config
                                            </button>
                                        </div>
                                    </div>
                                    <textarea id="configText" rows="12"
                                        class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-sm font-mono bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                                        readonly
                                        placeholder="Loading configuration..."></textarea>
                                    <div class="flex justify-between items-center mt-3">
                                        <span id="configType" class="text-xs font-medium text-blue-500">Clean Config</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="flex justify-end space-x-4 w-full pt-6 border-t border-gray-200">
                            <button onclick="amneziaApp.downloadClientConfig('${serverId}', '${clientId}')"
                                    class="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 shadow hover:shadow-lg transform hover:-translate-y-0.5">
                                <svg class="w-5 h-5 inline mr-2 -mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                                Download Config File (.conf)
                            </button>
                            <button onclick="amneziaApp.closeQRModal()"
                                    class="bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700 text-white px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 shadow hover:shadow-lg">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Close any existing modal first
        this.closeQRModal();
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Fetch client config and generate QR code
        this.fetchAndGenerateQRCode(serverId, clientId);
    }

    closeQRModal() {
        const existingModal = document.getElementById('qrModal');
        if (existingModal) {
            existingModal.remove();
        }
    }

    async fetchAndGenerateQRCode(serverId, clientId) {
        try {
            this.qrServerId = serverId;
            this.qrClientId = clientId;
            
            // Use the efficient endpoint that returns both versions
            const response = await fetch(`/api/servers/${serverId}/clients/${clientId}/config-both`);
            if (!response.ok) {
                throw new Error('Failed to fetch config');
            }
            
            const data = await response.json();
            this.currentCleanConfig = data.clean_config;
            this.currentFullConfig = data.full_config;
            this.currentConfigType = 'clean';
            this.currentClientName = data.client_name;
            
            // Display clean config text
            const configTextArea = document.getElementById('configText');
            if (configTextArea) {
                configTextArea.value = this.currentCleanConfig;
                this.updateConfigTypeLabel();
            }
            
            // Generate larger QR code from clean config
            const qrContainer = document.getElementById('qrcode');
            if (qrContainer) {
                qrContainer.innerHTML = ''; // Clear any existing QR code
                
                // Create larger QR code
                new QRCode(qrContainer, {
                    text: this.currentCleanConfig,
                    width: 300,
                    height: 300,
                    colorDark: "#000000",
                    colorLight: "#ffffff",
                    correctLevel: QRCode.CorrectLevel.H,
                    margin: 1
                });
            }
        } catch (error) {
            console.error('Error fetching config for QR code:', error);
            this.showTempMessage('Failed to generate QR code: ' + error.message, 'error');
            this.closeQRModal();
        }
    }

    updateConfigTypeLabel() {
        const configTypeLabel = document.getElementById('configType');
        if (configTypeLabel) {
            configTypeLabel.textContent = this.currentConfigType === 'clean' ? 'Clean Config' : 'Full Config';
        }
    }

    toggleConfigView() {
        const configTextArea = document.getElementById('configText');
        
        if (this.currentConfigType === 'clean') {
            // Switch to full config
            configTextArea.value = this.currentFullConfig;
            this.currentConfigType = 'full';
        } else {
            // Switch to clean config
            configTextArea.value = this.currentCleanConfig;
            this.currentConfigType = 'clean';
        }
        
        this.updateConfigTypeLabel();
    }

    downloadQRCode() {
        const qrContainer = document.getElementById('qrcode');
        if (!qrContainer) return;
        
        const canvas = qrContainer.querySelector('canvas');
        if (!canvas) return;
        
        // Create a temporary link to download the canvas as PNG
        const link = document.createElement('a');
        link.download = `${this.currentClientName.replace(/[^a-z0-9]/gi, '_')}_qr_code.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }

    copyConfigText() {
        const configTextArea = document.getElementById('configText');
        if (configTextArea) {
            configTextArea.select();
            configTextArea.setSelectionRange(0, 99999); // For mobile devices
            
            try {
                navigator.clipboard.writeText(configTextArea.value).then(() => {
                    this.showTempMessage('Configuration copied to clipboard!', 'success');
                }).catch(err => {
                    // Fallback for older browsers
                    document.execCommand('copy');
                    this.showTempMessage('Configuration copied to clipboard!', 'success');
                });
            } catch (err) {
                document.execCommand('copy');
                this.showTempMessage('Configuration copied to clipboard!', 'success');
            }
        }
    }

    copyToClipboard(text) {
        // Decode base64 text if it's the JSON data
        try {
            const decodedText = atob(text);
            const jsonData = JSON.parse(decodedText);
            text = jsonData.config_content || decodedText;
        } catch (e) {
            // If it's not base64 JSON, use the text as is
        }

        navigator.clipboard.writeText(text).then(() => {
            // Show a temporary notification
            this.showTempMessage('Configuration copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy: ', err);
            this.showTempMessage('Failed to copy to clipboard', 'error');
        });
    }

    showTempMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `fixed top-4 right-4 px-4 py-2 rounded text-white text-sm z-50 ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`;
        messageDiv.textContent = message;

        document.body.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    }
}

// Initialize the application
const amneziaApp = new AmneziaApp();