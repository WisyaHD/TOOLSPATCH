let statusCheckInterval = null;
let databaseJualList = {}; // Store multiple database jual
let memberDbDefault = '';
let memberCollectionDefault = '';
let jualDbDefault = '';
let jualCollectionDefault = '';
let beliDbDefault = '';
let beliCollectionDefault = '';
let hutangCollectionDefault = '';

function switchTab(tab) {
    // Remove active class from all tabs and tab-contents
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
    
    // Add active class to selected tab and content
    if (tab === 'config') {
        document.querySelectorAll('.tab')[0].classList.add('active');
        document.getElementById('config-tab').classList.add('active');
    } else {
        document.querySelectorAll('.tab')[1].classList.add('active');
        document.getElementById('process-tab').classList.add('active');
    }
}

function testConnection() {
    const uri = document.getElementById('mongodb-uri').value;
    if (!uri) {
        alert('Please enter MongoDB URI');
        return;
    }

    const statusDiv = document.getElementById('connection-status');
    statusDiv.style.display = 'block';
    statusDiv.className = 'config-status';
    statusDiv.innerHTML = '<span class="spinner"></span> Testing connection...';

    // Send URI via custom header, not in payload
    fetch('/api/test-connection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-MongoDB-URI': btoa(uri)  // Base64 encode for header safety
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusDiv.className = 'config-status connected';
            statusDiv.innerHTML = '✅ Connected successfully';
            populateMemberDatabaseDropdown(data.databases || []);
            populateJualDatabaseDropdown(data.databases || []);
            populateBeliDatabaseDropdown(data.databases || []);
        } else {
            statusDiv.className = 'config-status disconnected';
            statusDiv.innerHTML = '❌ Connection failed: ' + data.error;
        }
    })
    .catch(error => {
        statusDiv.className = 'config-status disconnected';
        statusDiv.innerHTML = '❌ Error: ' + error.message;
    });
}

function addDatabaseJual() {
    const kodeToko = document.getElementById('new-kode-toko').value.trim().toUpperCase();
    const dbName = document.getElementById('new-db-jual-name').value.trim();
    
    if (!kodeToko || !dbName) {
        alert('Harap isi Kode Toko dan Database Name');
        return;
    }
    
    // Add to list
    databaseJualList[kodeToko] = dbName;
    
    // Clear inputs
    document.getElementById('new-kode-toko').value = '';
    document.getElementById('new-db-jual-name').value = '';
    
    // Render list
    renderDatabaseJualList();
}

function removeDatabaseJual(kodeToko) {
    delete databaseJualList[kodeToko];
    renderDatabaseJualList();
}

function renderDatabaseJualList() {
    const container = document.getElementById('db-jual-list');
    
    if (Object.keys(databaseJualList).length === 0) {
        container.innerHTML = '<div style="color: #999; font-size: 13px; padding: 10px; text-align: center;">Belum ada database per cabang</div>';
        return;
    }
    
    let html = '';
    for (const [kodeToko, dbName] of Object.entries(databaseJualList)) {
        html += '<div class="db-item">' +
            '<div class="db-item-info">' +
            '<span class="db-item-code">' + kodeToko + '</span>' +
            '<span class="db-item-name">' + dbName + '</span>' +
            '</div>' +
            '<button type="button" class="btn-remove" onclick="removeDatabaseJual(\'' + kodeToko + '\')">' +
            '✕ Hapus' +
            '</button>' +
            '</div>';
    }
    container.innerHTML = html;
}

function saveConfig() {
    const dbMemberSelect = document.getElementById('db-member');
    const collectionMemberSelect = document.getElementById('collection-member');
    const dbMemberValue = (dbMemberSelect && dbMemberSelect.value) || memberDbDefault || '';
    const collectionMemberValue = (collectionMemberSelect && collectionMemberSelect.value) || memberCollectionDefault || '';
    const dbJualSelect = document.getElementById('db-jual');
    const collectionJualSelect = document.getElementById('collection-jual');
    const dbJualValue = (dbJualSelect && dbJualSelect.value) || jualDbDefault || '';
    const collectionJualValue = (collectionJualSelect && collectionJualSelect.value) || jualCollectionDefault || '';
    const dbBeliSelect = document.getElementById('db-beli');
    const collectionBeliSelect = document.getElementById('collection-beli');
    const collectionHutangSelect = document.getElementById('collection-hutang');
    const dbBeliValue = (dbBeliSelect && dbBeliSelect.value) || beliDbDefault || '';
    const collectionBeliValue = (collectionBeliSelect && collectionBeliSelect.value) || beliCollectionDefault || '';
    const collectionHutangValue = (collectionHutangSelect && collectionHutangSelect.value) || hutangCollectionDefault || '';

    const config = {
        mongodb_uri: document.getElementById('mongodb-uri').value,
        db_member: dbMemberValue,
        db_jual: dbJualValue,
        db_beli: dbBeliValue,
        collection_member: collectionMemberValue,
        collection_jual: collectionJualValue,
        collection_beli: collectionBeliValue,
        collection_hutang: collectionHutangValue,
        db_jual_branches: databaseJualList  // Include multiple databases
    };

    // Validate required fields
    if (!config.mongodb_uri || !config.db_member || !config.db_jual) {
        alert('Please fill in all required fields (marked with *)');
        return;
    }

    const saveStatus = document.getElementById('save-status');
    saveStatus.className = 'status-message status-info';
    saveStatus.innerHTML = '<span class="spinner"></span> Saving configuration...';
    saveStatus.style.display = 'block';

    fetch('/api/save-config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            saveStatus.className = 'status-message status-success';
            saveStatus.innerHTML = '✅ Configuration saved successfully!';
            setTimeout(() => {
                saveStatus.style.display = 'none';
            }, 3000);
        } else {
            saveStatus.className = 'status-message status-error';
            saveStatus.innerHTML = '❌ Failed to save: ' + data.error;
        }
    })
    .catch(error => {
        saveStatus.className = 'status-message status-error';
        saveStatus.innerHTML = '❌ Error: ' + error.message;
    });
}

function runPatch() {
    const fileInput = document.getElementById('patch-file');
    const fileSelect = document.getElementById('patch-file-select');
    const statusDiv = document.getElementById('status-message');
    
    // Check if file is uploaded from local computer
    if (fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        statusDiv.className = 'status-message status-info';
        statusDiv.innerHTML = '<span class="spinner"></span> Uploading and starting patch process...';
        
        fetch('/api/patch-upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Server error: ${response.status} - ${text.substring(0, 100)}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                startStatusCheck();
            } else {
                statusDiv.className = 'status-message status-error';
                statusDiv.innerHTML = '❌ Error: ' + data.error;
            }
        })
        .catch(error => {
            statusDiv.className = 'status-message status-error';
            statusDiv.innerHTML = '❌ Error: ' + error.message;
        });
    } else if (fileSelect.value) {
        // Use server file selection
        const file = fileSelect.value;
        
        statusDiv.className = 'status-message status-info';
        statusDiv.innerHTML = '<span class="spinner"></span> Starting patch process...';

        fetch('/api/patch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({input_file: file})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                startStatusCheck();
            } else {
                statusDiv.className = 'status-message status-error';
                statusDiv.innerHTML = '❌ Error: ' + data.error;
            }
        })
        .catch(error => {
            statusDiv.className = 'status-message status-error';
            statusDiv.innerHTML = '❌ Error: ' + error.message;
        });
    } else {
        alert('Please select a file from your computer or from the server');
    }
}

function runTransform() {
    const fileInput = document.getElementById('transform-file');
    const fileSelect = document.getElementById('transform-file-select');
    const statusDiv = document.getElementById('status-message');
    
    // Check if file is uploaded from local computer
    if (fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        statusDiv.className = 'status-message status-info';
        statusDiv.innerHTML = '<span class="spinner"></span> Uploading and starting transform process...';
        
        fetch('/api/transform-upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Server error: ${response.status} - ${text.substring(0, 100)}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                startStatusCheck();
            } else {
                statusDiv.className = 'status-message status-error';
                statusDiv.innerHTML = '❌ Error: ' + data.error;
            }
        })
        .catch(error => {
            statusDiv.className = 'status-message status-error';
            statusDiv.innerHTML = '❌ Error: ' + error.message;
        });
    } else if (fileSelect.value) {
        // Use server file selection
        const file = fileSelect.value;
        
        statusDiv.className = 'status-message status-info';
        statusDiv.innerHTML = '<span class="spinner"></span> Starting transform process...';

        fetch('/api/transform', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({input_file: file})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                startStatusCheck();
            } else {
                statusDiv.className = 'status-message status-error';
                statusDiv.innerHTML = '❌ Error: ' + data.error;
            }
        })
        .catch(error => {
            statusDiv.className = 'status-message status-error';
            statusDiv.innerHTML = '❌ Error: ' + error.message;
        });
    } else {
        alert('Please select a file from your computer or from the server');
    }
}

function runPatchNoFaktur() {
    const fileInput = document.getElementById('patch-no-faktur-file');
    const fileSelect = document.getElementById('patch-no-faktur-file-select');
    const statusDiv = document.getElementById('status-message');
    
    // Check if file is uploaded from local computer
    if (fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        statusDiv.className = 'status-message status-info';
        statusDiv.innerHTML = '<span class="spinner"></span> Uploading and starting patch no_faktur process...';
        
        fetch('/api/patch-no-faktur-upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Server error: ${response.status} - ${text.substring(0, 100)}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                startStatusCheck();
            } else {
                statusDiv.className = 'status-message status-error';
                statusDiv.innerHTML = '❌ Error: ' + data.error;
            }
        })
        .catch(error => {
            statusDiv.className = 'status-message status-error';
            statusDiv.innerHTML = '❌ Error: ' + error.message;
        });
    } else if (fileSelect.value) {
        // Use server file selection
        statusDiv.className = 'status-message status-info';
        statusDiv.innerHTML = '<span class="spinner"></span> Starting patch no_faktur process...';

        fetch('/api/patch-no-faktur', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({input_file: fileSelect.value})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                startStatusCheck();
            } else {
                statusDiv.className = 'status-message status-error';
                statusDiv.innerHTML = '❌ Error: ' + data.error;
            }
        })
        .catch(error => {
            statusDiv.className = 'status-message status-error';
            statusDiv.innerHTML = '❌ Error: ' + error.message;
        });
    } else {
        statusDiv.className = 'status-message status-error';
        statusDiv.innerHTML = '❌ Error: Pilih file dari komputer atau server';
    }
}

function runPatchNoFakturOptimized() {
    const fileInput = document.getElementById('patch-no-faktur-file');
    const fileSelect = document.getElementById('patch-no-faktur-file-select');
    const statusDiv = document.getElementById('status-message');
    
    // Check if file is uploaded from local computer
    if (fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        statusDiv.className = 'status-message status-info';
        statusDiv.innerHTML = '<span class="spinner"></span> Uploading and starting OPTIMIZED patch no_faktur process (for large files)...';
        
        fetch('/api/patch-no-faktur-upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Server error: ${response.status} - ${text.substring(0, 100)}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Use optimized endpoint instead
                fetch('/api/patch-no-faktur-optimized', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({input_file: data.filename, batch_size: 2000})
                })
                .then(response => response.json())
                .then(data2 => {
                    if (data2.success) {
                        startStatusCheck();
                    } else {
                        statusDiv.className = 'status-message status-error';
                        statusDiv.innerHTML = '❌ Error: ' + data2.error;
                    }
                });
            } else {
                statusDiv.className = 'status-message status-error';
                statusDiv.innerHTML = '❌ Error: ' + data.error;
            }
        })
        .catch(error => {
            statusDiv.className = 'status-message status-error';
            statusDiv.innerHTML = '❌ Error: ' + error.message;
        });
    } else if (fileSelect.value) {
        // Use server file selection
        statusDiv.className = 'status-message status-info';
        statusDiv.innerHTML = '<span class="spinner"></span> Starting OPTIMIZED patch no_faktur process (for large files)...';

        fetch('/api/patch-no-faktur-optimized', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({input_file: fileSelect.value, batch_size: 2000})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                startStatusCheck();
            } else {
                statusDiv.className = 'status-message status-error';
                statusDiv.innerHTML = '❌ Error: ' + data.error;
            }
        })
        .catch(error => {
            statusDiv.className = 'status-message status-error';
            statusDiv.innerHTML = '❌ Error: ' + error.message;
        });
    } else {
        statusDiv.className = 'status-message status-error';
        statusDiv.innerHTML = '❌ Error: Pilih file dari komputer atau server';
    }
}

function resetStatus() {
    const statusDiv = document.getElementById('status-message');
    statusDiv.className = 'status-message status-info';
    statusDiv.innerHTML = '<span class="spinner"></span> Resetting status...';
    
    fetch('/api/reset-status', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusDiv.className = 'status-message status-success';
            statusDiv.innerHTML = '✅ Status reset successfully! Ready for new process';
            document.getElementById('progress-fill').style.width = '0%';
            
            if (statusCheckInterval) {
                clearInterval(statusCheckInterval);
            }
        } else {
            statusDiv.className = 'status-message status-error';
            statusDiv.innerHTML = '❌ Error resetting status: ' + data.message;
        }
    })
    .catch(error => {
        statusDiv.className = 'status-message status-error';
        statusDiv.innerHTML = '❌ Error: ' + error.message;
    });
}

function startStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(checkStatus, 1000);
}

function checkStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            const progressFill = document.getElementById('progress-fill');
            const statusDiv = document.getElementById('status-message');
            
            progressFill.style.width = data.progress + '%';
            
            if (data.is_processing) {
                statusDiv.className = 'status-message status-info';
                statusDiv.innerHTML = '<span class="spinner"></span> ' + data.message;
            } else if (data.error) {
                statusDiv.className = 'status-message status-error';
                statusDiv.innerHTML = '❌ Error: ' + data.error;
                clearInterval(statusCheckInterval);
            } else if (data.output_file) {
                statusDiv.className = 'status-message status-success';
                statusDiv.innerHTML = '✅ ' + data.message + ' - Output: ' + data.output_file;
                clearInterval(statusCheckInterval);
                
                // Refresh download table
                loadProcessedFiles();
                
                // Auto-download the file
                autoDownloadFile(data.output_file);
            }
        });
}

// Load current config on page load
window.addEventListener('load', function() {
    fetch('/api/get-config')
        .then(response => response.json())
        .then(data => {
            if (data.config) {
                document.getElementById('mongodb-uri').value = data.config.MONGODB_URI || 'mongodb://localhost:27017/';
                memberDbDefault = data.config.DB_MEMBER || 'db_hdpayn_asli';
                jualDbDefault = data.config.DB_JUAL || 'db_hdpayn_asli';
                beliDbDefault = data.config.DB_BELI || 'db_hdpayn_asli';
                memberCollectionDefault = data.config.COLLECTION_TT_MEMBER || 'tt_member';
                jualCollectionDefault = data.config.COLLECTION_TT_JUAL_DETAIL || 'tt_jual_detail';
                beliCollectionDefault = data.config.COLLECTION_TT_BELI_DETAIL || 'tt_beli_detail';
                hutangCollectionDefault = data.config.COLLECTION_TT_HUTANG_DETAIL || 'tt_hutang_detail';
                
                // Load multiple database jual
                if (data.config.DB_JUAL_BRANCHES) {
                    databaseJualList = data.config.DB_JUAL_BRANCHES;
                    renderDatabaseJualList();
                }
            }
        })
        .catch(function(error) {
            console.error('Error loading config:', error);
        });
    
    // Load processed files
    loadProcessedFiles();
});

function populateMemberDatabaseDropdown(databases) {
    const dbWrapper = document.getElementById('db-member-wrapper');
    const collectionWrapper = document.getElementById('collection-member-wrapper');
    const hint = document.getElementById('db-member-hint');
    const dbSelect = document.getElementById('db-member');
    const collectionSelect = document.getElementById('collection-member');
    const dbSearch = document.getElementById('db-member-search');
    const collectionSearch = document.getElementById('collection-member-search');

    if (!dbSelect || !collectionSelect) {
        return;
    }

    // Show dropdowns
    dbWrapper.style.display = 'block';
    hint.style.display = 'none';

    // Populate database options
    dbSelect.innerHTML = '<option value="">-- Select Database --</option>';
    databases.forEach(dbName => {
        const option = document.createElement('option');
        option.value = dbName;
        option.textContent = dbName;
        dbSelect.appendChild(option);
    });

    if (dbSearch) {
        dbSearch.value = '';
        dbSearch.oninput = function() {
            filterSelectOptions(dbSelect, dbSearch.value);
        };
    }

    // Set default selection if available
    if (memberDbDefault && databases.includes(memberDbDefault)) {
        dbSelect.value = memberDbDefault;
        loadMemberCollections(memberDbDefault);
    } else {
        collectionWrapper.style.display = 'none';
        collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
    }

    dbSelect.onchange = function() {
        const selectedDb = dbSelect.value;
        if (selectedDb) {
            loadMemberCollections(selectedDb);
        } else {
            collectionWrapper.style.display = 'none';
            collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
        }
    };

    if (collectionSearch) {
        collectionSearch.value = '';
        collectionSearch.oninput = function() {
            filterSelectOptions(collectionSelect, collectionSearch.value);
        };
    }
}

function populateJualDatabaseDropdown(databases) {
    const dbWrapper = document.getElementById('db-jual-wrapper');
    const collectionWrapper = document.getElementById('collection-jual-wrapper');
    const hint = document.getElementById('db-jual-hint');
    const dbSelect = document.getElementById('db-jual');
    const collectionSelect = document.getElementById('collection-jual');
    const dbSearch = document.getElementById('db-jual-search');
    const collectionSearch = document.getElementById('collection-jual-search');

    if (!dbSelect || !collectionSelect) {
        return;
    }

    dbWrapper.style.display = 'block';
    hint.style.display = 'none';

    dbSelect.innerHTML = '<option value="">-- Select Database --</option>';
    databases.forEach(dbName => {
        const option = document.createElement('option');
        option.value = dbName;
        option.textContent = dbName;
        dbSelect.appendChild(option);
    });

    if (dbSearch) {
        dbSearch.value = '';
        dbSearch.oninput = function() {
            filterSelectOptions(dbSelect, dbSearch.value);
        };
    }

    if (jualDbDefault && databases.includes(jualDbDefault)) {
        dbSelect.value = jualDbDefault;
        loadJualCollections(jualDbDefault);
    } else {
        collectionWrapper.style.display = 'none';
        collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
    }

    dbSelect.onchange = function() {
        const selectedDb = dbSelect.value;
        if (selectedDb) {
            loadJualCollections(selectedDb);
        } else {
            collectionWrapper.style.display = 'none';
            collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
        }
    };

    if (collectionSearch) {
        collectionSearch.value = '';
        collectionSearch.oninput = function() {
            filterSelectOptions(collectionSelect, collectionSearch.value);
        };
    }
}

function populateBeliDatabaseDropdown(databases) {
    const dbWrapper = document.getElementById('db-beli-wrapper');
    const collectionWrapper = document.getElementById('collection-beli-wrapper');
    const hutangWrapper = document.getElementById('collection-hutang-wrapper');
    const hint = document.getElementById('db-beli-hint');
    const dbSelect = document.getElementById('db-beli');
    const collectionSelect = document.getElementById('collection-beli');
    const hutangSelect = document.getElementById('collection-hutang');
    const dbSearch = document.getElementById('db-beli-search');
    const collectionSearch = document.getElementById('collection-beli-search');
    const hutangSearch = document.getElementById('collection-hutang-search');

    if (!dbSelect || !collectionSelect || !hutangSelect) {
        return;
    }

    dbWrapper.style.display = 'block';
    hint.style.display = 'none';

    dbSelect.innerHTML = '<option value="">-- Select Database --</option>';
    databases.forEach(dbName => {
        const option = document.createElement('option');
        option.value = dbName;
        option.textContent = dbName;
        dbSelect.appendChild(option);
    });

    if (dbSearch) {
        dbSearch.value = '';
        dbSearch.oninput = function() {
            filterSelectOptions(dbSelect, dbSearch.value);
        };
    }

    if (beliDbDefault && databases.includes(beliDbDefault)) {
        dbSelect.value = beliDbDefault;
        loadBeliCollections(beliDbDefault);
    } else {
        collectionWrapper.style.display = 'none';
        hutangWrapper.style.display = 'none';
        collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
        hutangSelect.innerHTML = '<option value="">-- Select Collection --</option>';
    }

    dbSelect.onchange = function() {
        const selectedDb = dbSelect.value;
        if (selectedDb) {
            loadBeliCollections(selectedDb);
        } else {
            collectionWrapper.style.display = 'none';
            hutangWrapper.style.display = 'none';
            collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
            hutangSelect.innerHTML = '<option value="">-- Select Collection --</option>';
        }
    };

    if (collectionSearch) {
        collectionSearch.value = '';
        collectionSearch.oninput = function() {
            filterSelectOptions(collectionSelect, collectionSearch.value);
        };
    }

    if (hutangSearch) {
        hutangSearch.value = '';
        hutangSearch.oninput = function() {
            filterSelectOptions(hutangSelect, hutangSearch.value);
        };
    }
}

function loadBeliCollections(dbName) {
    const collectionWrapper = document.getElementById('collection-beli-wrapper');
    const hutangWrapper = document.getElementById('collection-hutang-wrapper');
    const collectionSelect = document.getElementById('collection-beli');
    const hutangSelect = document.getElementById('collection-hutang');
    const collectionSearch = document.getElementById('collection-beli-search');
    const hutangSearch = document.getElementById('collection-hutang-search');

    if (!dbName) {
        return;
    }

    fetch('/api/list-collections', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({db_name: dbName})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            collectionWrapper.style.display = 'block';
            hutangWrapper.style.display = 'block';
            collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
            hutangSelect.innerHTML = '<option value="">-- Select Collection --</option>';
            (data.collections || []).forEach(colName => {
                const option = document.createElement('option');
                option.value = colName;
                option.textContent = colName;
                collectionSelect.appendChild(option);

                const hutangOption = document.createElement('option');
                hutangOption.value = colName;
                hutangOption.textContent = colName;
                hutangSelect.appendChild(hutangOption);
            });

            if (collectionSearch) {
                collectionSearch.value = '';
                collectionSearch.oninput = function() {
                    filterSelectOptions(collectionSelect, collectionSearch.value);
                };
            }

            if (hutangSearch) {
                hutangSearch.value = '';
                hutangSearch.oninput = function() {
                    filterSelectOptions(hutangSelect, hutangSearch.value);
                };
            }

            if (beliCollectionDefault && data.collections.includes(beliCollectionDefault)) {
                collectionSelect.value = beliCollectionDefault;
            }

            if (hutangCollectionDefault && data.collections.includes(hutangCollectionDefault)) {
                hutangSelect.value = hutangCollectionDefault;
            }
        } else {
            collectionWrapper.style.display = 'none';
            hutangWrapper.style.display = 'none';
            collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
            hutangSelect.innerHTML = '<option value="">-- Select Collection --</option>';
            alert('Failed to load collections: ' + data.error);
        }
    })
    .catch(error => {
        collectionWrapper.style.display = 'none';
        hutangWrapper.style.display = 'none';
        collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
        hutangSelect.innerHTML = '<option value="">-- Select Collection --</option>';
        alert('Failed to load collections: ' + error.message);
    });
}

function loadJualCollections(dbName) {
    const collectionWrapper = document.getElementById('collection-jual-wrapper');
    const collectionSelect = document.getElementById('collection-jual');
    const collectionSearch = document.getElementById('collection-jual-search');

    if (!dbName) {
        return;
    }

    fetch('/api/list-collections', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({db_name: dbName})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            collectionWrapper.style.display = 'block';
            collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
            (data.collections || []).forEach(colName => {
                const option = document.createElement('option');
                option.value = colName;
                option.textContent = colName;
                collectionSelect.appendChild(option);
            });

            if (collectionSearch) {
                collectionSearch.value = '';
                collectionSearch.oninput = function() {
                    filterSelectOptions(collectionSelect, collectionSearch.value);
                };
            }

            if (jualCollectionDefault && data.collections.includes(jualCollectionDefault)) {
                collectionSelect.value = jualCollectionDefault;
            }
        } else {
            collectionWrapper.style.display = 'none';
            collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
            alert('Failed to load collections: ' + data.error);
        }
    })
    .catch(error => {
        collectionWrapper.style.display = 'none';
        collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
        alert('Failed to load collections: ' + error.message);
    });
}

function loadMemberCollections(dbName) {
    const collectionWrapper = document.getElementById('collection-member-wrapper');
    const collectionSelect = document.getElementById('collection-member');
    const collectionSearch = document.getElementById('collection-member-search');

    if (!dbName) {
        return;
    }

    fetch('/api/list-collections', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({db_name: dbName})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            collectionWrapper.style.display = 'block';
            collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
            (data.collections || []).forEach(colName => {
                const option = document.createElement('option');
                option.value = colName;
                option.textContent = colName;
                collectionSelect.appendChild(option);
            });

            if (collectionSearch) {
                collectionSearch.value = '';
                collectionSearch.oninput = function() {
                    filterSelectOptions(collectionSelect, collectionSearch.value);
                };
            }

            if (memberCollectionDefault && data.collections.includes(memberCollectionDefault)) {
                collectionSelect.value = memberCollectionDefault;
            }
        } else {
            collectionWrapper.style.display = 'none';
            collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
            alert('Failed to load collections: ' + data.error);
        }
    })
    .catch(error => {
        collectionWrapper.style.display = 'none';
        collectionSelect.innerHTML = '<option value="">-- Select Collection --</option>';
        alert('Failed to load collections: ' + error.message);
    });
}

function filterSelectOptions(selectEl, query) {
    if (!selectEl) return;
    const q = (query || '').toLowerCase();
    Array.from(selectEl.options).forEach(option => {
        if (option.value === '') {
            option.hidden = false;
            return;
        }
        option.hidden = q && !option.textContent.toLowerCase().includes(q);
    });
}

function loadProcessedFiles() {
    fetch('/api/processed-files')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.files && data.files.length > 0) {
                renderDownloadTable(data.files);
            }
        })
        .catch(error => {
            console.error('Error loading processed files:', error);
        });
}

function renderDownloadTable(files) {
    const tbody = document.getElementById('download-table-body');
    
    // Filter out empty files (0 bytes)
    const validFiles = files.filter(file => file.size > 0);
    
    if (!validFiles || validFiles.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #999; padding: 20px;">Belum ada file yang diproses</td></tr>';
        return;
    }
    
    let html = '';
    validFiles.forEach(file => {
        let badgeClass = 'badge-patch';
        if (file.type === 'transform') {
            badgeClass = 'badge-transform';
        } else if (file.type === 'patch_no_faktur') {
            badgeClass = 'badge-patch_no_faktur';
        }
        const fileSize = formatFileSize(file.size);
        
        html += '<tr>' +
            '<td><strong>' + file.filename + '</strong></td>' +
            '<td><span class="badge ' + badgeClass + '">' + file.type.toUpperCase().replace(/_/g, ' ') + '</span></td>' +
            '<td>' + file.timestamp + '</td>' +
            '<td>' + fileSize + '</td>' +
            '<td>' +
            '<button class="btn-download" onclick="downloadFile(\'' + file.filepath + '\', \'' + file.filename + '\')">' +
            '📥 Download' +
            '</button>' +
            '</td>' +
            '</tr>';
    });
    
    tbody.innerHTML = html;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function downloadFile(filepath, filename) {
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = '/api/download/' + encodeURIComponent(filepath);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function autoDownloadFile(filepath) {
    // Auto-download after processing complete
    const filename = filepath.split('/').pop();
    setTimeout(() => {
        downloadFile(filepath, filename);
    }, 500); // Small delay to ensure file is ready
}
