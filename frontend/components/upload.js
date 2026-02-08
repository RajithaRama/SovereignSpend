// Upload Component

async function loadUploadView() {
    try {
        const accounts = await api.get('/api/accounts/');
        state.accounts = accounts;
        populateStatementAccountSelect();
        initializeUploadZones();
    } catch (error) {
        console.error('Error loading upload view:', error);
    }
}

function populateStatementAccountSelect() {
    const select = document.getElementById('statement-account');
    select.innerHTML = '<option value="">Choose Account...</option>' +
        state.accounts.map(acc => `<option value="${acc.id}">${acc.name}</option>`).join('');
}

function initializeUploadZones() {
    // Invoice upload
    const invoiceZone = document.getElementById('invoice-upload-zone');
    const invoiceInput = document.getElementById('invoice-file-input');

    invoiceZone.addEventListener('click', () => invoiceInput.click());

    invoiceZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        invoiceZone.classList.add('drag-over');
    });

    invoiceZone.addEventListener('dragleave', () => {
        invoiceZone.classList.remove('drag-over');
    });

    invoiceZone.addEventListener('drop', (e) => {
        e.preventDefault();
        invoiceZone.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadInvoice(files[0]);
        }
    });

    invoiceInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadInvoice(e.target.files[0]);
        }
    });

    // Bank statement upload
    const statementZone = document.getElementById('statement-upload-zone');
    const statementInput = document.getElementById('statement-file-input');

    statementZone.addEventListener('click', () => statementInput.click());

    statementZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        statementZone.classList.add('drag-over');
    });

    statementZone.addEventListener('dragleave', () => {
        statementZone.classList.remove('drag-over');
    });

    statementZone.addEventListener('drop', (e) => {
        e.preventDefault();
        statementZone.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadBankStatement(files[0]);
        }
    });

    statementInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadBankStatement(e.target.files[0]);
        }
    });
}

async function uploadInvoice(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showNotification('Only PDF files are supported', 'error');
        return;
    }

    const statusDiv = document.getElementById('invoice-upload-status');
    statusDiv.innerHTML = `
        <div class="glass-card" style="padding: 1rem;">
            <div class="spinner"></div>
            <p style="color: var(--text-secondary); text-align: center; margin-top: 1rem;">
                Uploading and processing invoice with AI...
            </p>
        </div>
    `;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const result = await api.uploadFile('/api/upload/invoice', formData);

        statusDiv.innerHTML = `
            <div class="glass-card" style="padding: 1rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <h4 style="margin-bottom: 0.5rem;">✓ Invoice Uploaded Successfully!</h4>
                <p style="font-size: 0.875rem; opacity: 0.9;">File: ${result.filename}</p>
                <p style="font-size: 0.875rem; opacity: 0.9; margin-top: 0.5rem;">
                    Extracted text preview: ${result.extracted_text ? result.extracted_text.substring(0, 200) + '...' : 'N/A'}
                </p>
            </div>
        `;

        showNotification('Invoice uploaded and processed successfully!');

        // Clear the input
        document.getElementById('invoice-file-input').value = '';

        // Clear status after 5 seconds
        setTimeout(() => {
            statusDiv.innerHTML = '';
        }, 5000);
    } catch (error) {
        console.error('Error uploading invoice:', error);
        statusDiv.innerHTML = `
            <div class="glass-card" style="padding: 1rem; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <h4>✗ Upload Failed</h4>
                <p style="font-size: 0.875rem; opacity: 0.9;">${error.message}</p>
            </div>
        `;
    }
}

async function uploadBankStatement(file, force = false) {
    const accountId = document.getElementById('statement-account').value;

    if (!accountId) {
        showNotification('Please select an account first', 'error');
        return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf') && !file.name.toLowerCase().endsWith('.csv')) {
        showNotification('Only PDF and CSV files are supported', 'error');
        return;
    }

    const statusDiv = document.getElementById('statement-upload-status');
    statusDiv.innerHTML = `
        <div class="glass-card" style="padding: 1rem;">
            <div class="spinner"></div>
            <p style="color: var(--text-secondary); text-align: center; margin-top: 1rem;">
                Uploading and parsing bank statement with AI...<br>
                This may take a moment.
            </p>
        </div>
    `;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('account_id', accountId);

    const bankSelect = document.getElementById('statement-bank');
    if (bankSelect) {
        formData.append('bank_name', bankSelect.value);
    }

    if (force) {
        formData.append('force', 'true');
    }

    try {
        const result = await api.uploadFile('/api/upload/bank-statement', formData);

        // Check for foreign transactions
        if (result.foreign_transactions && result.foreign_transactions.length > 0) {
            // Show foreign currency modal
            showForeignCurrencyModal(result.foreign_transactions, accountId);

            // Clear the input
            document.getElementById('statement-file-input').value = '';

            // Show partial success message
            statusDiv.innerHTML = `
                <div class="glass-card" style="padding: 1rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                    <h4 style="margin-bottom: 0.5rem;">✓ EUR Transactions Processed!</h4>
                    <p style="font-size: 0.875rem; opacity: 0.9;">
                        Created ${result.transactions_created} EUR transactions from ${result.raw_transactions} parsed entries
                    </p>
                    <p style="font-size: 0.875rem; opacity: 0.9; margin-top: 0.5rem;">
                        ⚠️ ${result.foreign_transactions.length} foreign currency transactions require verification
                    </p>
                </div>
            `;

            return; // Don't clear status or show full success
        }

        statusDiv.innerHTML = `
            <div class="glass-card" style="padding: 1rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <h4 style="margin-bottom: 0.5rem;">✓ Bank Statement Processed!</h4>
                <p style="font-size: 0.875rem; opacity: 0.9;">
                    Created ${result.transactions_created} transactions from ${result.raw_transactions} parsed entries
                </p>
                <div id="upload-message-area">
                    <p style="font-size: 0.875rem; opacity: 0.9; margin-top: 0.5rem;">
                        ${result.message}
                    </p>
                </div>
            </div>
            
            ${result.duplicates_found && result.duplicates_found.length > 0 ? `
            <div class="glass-card" style="padding: 1rem; margin-top: 1rem; border: 1px solid rgba(245, 101, 101, 0.3);">
                <h4 style="margin-bottom: 0.5rem; color: #f56565;">⚠️ ${result.duplicates_found.length} Duplicates Skipped</h4>
                <div style="max-height: 200px; overflow-y: auto; margin-top: 0.5rem;">
                    ${result.duplicates_found.map((dup, index) => `
                        <div style="background: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-size: 0.8rem;">
                                <div>${dup.date} - ${dup.description}</div>
                                <div style="color: var(--text-secondary);">${dup.amount < 0 ? '-' : ''}$${Math.abs(dup.amount).toFixed(2)}</div>
                            </div>
                            <button class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.7rem;" onclick="forceAddDuplicate(${index})">Add Anyway</button>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        `;

        // Store duplicates in a temp global for the force add function
        window.lastUploadDuplicates = result.duplicates_found || [];
        window.lastUploadAccountId = accountId; // From the scoped variable



        showNotification(`Bank statement processed! ${result.transactions_created} transactions created.`);

        // Clear the input
        document.getElementById('statement-file-input').value = '';

        // Clear status after 5 seconds
        setTimeout(() => {
            statusDiv.innerHTML = '';
        }, 5000);
    } catch (error) {
        console.error('Error uploading bank statement:', error);

        // Handle 409 Duplicate specifically
        if (error.message && (error.message.includes('409') || error.message.includes('Duplicate'))) {
            statusDiv.innerHTML = `
                <div class="glass-card" style="padding: 1rem; border: 1px solid #ecc94b;">
                    <h4 style="color: #ecc94b; margin-bottom: 0.5rem;">⚠️ Duplicate File Detected</h4>
                    <p style="font-size: 0.875rem; opacity: 0.9; margin-bottom: 1rem;">
                        This file has already been uploaded. Do you want to process it again?
                    </p>
                    <div style="display: flex; gap: 1rem;">
                        <button class="btn btn-secondary" onclick="document.getElementById('statement-upload-status').innerHTML = '';">Cancel</button>
                        <button class="btn btn-primary" id="force-upload-btn">Process Again</button>
                    </div>
                </div>
            `;

            // Attach listener to the new button
            document.getElementById('force-upload-btn').addEventListener('click', () => {
                uploadBankStatement(file, true);
            });
            return;
        }

        statusDiv.innerHTML = `
            <div class="glass-card" style="padding: 1rem; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <h4>✗ Upload Failed</h4>
                <p style="font-size: 0.875rem; opacity: 0.9;">${error.message}</p>
            </div>
        `;
    }
}

async function forceAddDuplicate(index) {
    const dup = window.lastUploadDuplicates[index];
    if (!dup) return;

    try {
        const data = {
            date: dup.date,
            account_id: parseInt(window.lastUploadAccountId),
            amount: Math.abs(dup.amount),
            type: dup.type,
            description: dup.description,
            category: dup.category
        };

        await api.post('/api/transactions/', data);

        showNotification('Transaction added manually.');

        // Disable the button to prevent double add?
        // Simple reload to refresh balances and list
        if (typeof loadUploadView === 'function') {
            // Maybe just refresh account list?
        }

    } catch (error) {
        console.error('Error adding duplicate:', error);
        showNotification('Error adding transaction', 'error');
    }
}

function showForeignCurrencyModal(foreignTransactions, accountId) {
    const modal = document.getElementById('foreign-currency-modal');
    const tableContainer = document.getElementById('foreign-transactions-table');

    // Build the table HTML
    tableContainer.innerHTML = `
        <div style="margin-bottom: 1rem; padding: 0.75rem; background: rgba(245, 101, 101, 0.1); border-radius: var(--radius-md); border: 1px solid rgba(245, 101, 101, 0.3);">
            <div style="display: grid; grid-template-columns: 100px 1fr 100px 80px 150px; gap: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--text-secondary);">
                <div>Date</div>
                <div>Description</div>
                <div>Amount</div>
                <div>Currency</div>
                <div>EUR Amount</div>
            </div>
        </div>
        ${foreignTransactions.map((trans, index) => `
            <div class="foreign-transaction-row" data-index="${index}">
                <div class="date">${trans.date}</div>
                <div class="description">${trans.description}</div>
                <div class="amount">${trans.amount.toFixed(2)}</div>
                <div class="currency-badge">${trans.currency}</div>
                <input 
                    type="number" 
                    step="0.01" 
                    class="eur-input" 
                    data-index="${index}"
                    placeholder="0.00"
                    style="width: 100%;"
                />
            </div>
        `).join('')}
    `;

    // Store data for import
    window.foreignTransactionsData = foreignTransactions;
    window.foreignTransactionsAccountId = accountId;

    // Show modal
    modal.classList.remove('hidden');

    // Setup event listeners
    const cancelBtn = document.getElementById('cancel-foreign-btn');
    const importBtn = document.getElementById('import-foreign-btn');

    // Remove old listeners
    const newCancelBtn = cancelBtn.cloneNode(true);
    const newImportBtn = importBtn.cloneNode(true);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    importBtn.parentNode.replaceChild(newImportBtn, importBtn);

    // Add new listeners
    newCancelBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        window.foreignTransactionsData = null;
        window.foreignTransactionsAccountId = null;
    });

    newImportBtn.addEventListener('click', importForeignTransactions);

    // Close on overlay click
    const overlay = modal.querySelector('.modal-overlay');
    overlay.addEventListener('click', () => {
        modal.classList.add('hidden');
        window.foreignTransactionsData = null;
        window.foreignTransactionsAccountId = null;
    });
}

async function importForeignTransactions() {
    const foreignTransactions = window.foreignTransactionsData;
    const accountId = window.foreignTransactionsAccountId;

    if (!foreignTransactions || !accountId) {
        showNotification('No foreign transactions to import', 'error');
        return;
    }

    // Collect transactions with EUR amounts
    const transactionsToImport = [];
    const inputs = document.querySelectorAll('.eur-input');

    inputs.forEach((input, index) => {
        const eurAmount = parseFloat(input.value);
        if (!isNaN(eurAmount) && eurAmount !== 0) {
            const originalTrans = foreignTransactions[index];
            transactionsToImport.push({
                date: originalTrans.date,
                description: originalTrans.description,
                amount: eurAmount
            });
        }
    });

    if (transactionsToImport.length === 0) {
        showNotification('Please enter EUR amounts for at least one transaction', 'error');
        return;
    }

    try {
        // Show loading state
        const importBtn = document.getElementById('import-foreign-btn');
        importBtn.disabled = true;
        importBtn.textContent = 'Importing...';

        // Call the API
        const result = await api.post('/api/transactions/import-foreign', {
            account_id: parseInt(accountId),
            transactions: transactionsToImport
        });

        // Close modal
        const modal = document.getElementById('foreign-currency-modal');
        modal.classList.add('hidden');

        // Show success notification
        showNotification(`Successfully imported ${result.transactions_created} foreign transactions!`);

        // Show errors if any
        if (result.errors && result.errors.length > 0) {
            console.warn('Import errors:', result.errors);
            showNotification(`${result.errors.length} transactions had errors`, 'error');
        }

        // Clear stored data
        window.foreignTransactionsData = null;
        window.foreignTransactionsAccountId = null;

        // Clear the upload status after a delay
        setTimeout(() => {
            const statusDiv = document.getElementById('statement-upload-status');
            if (statusDiv) {
                statusDiv.innerHTML = '';
            }
        }, 3000);

    } catch (error) {
        console.error('Error importing foreign transactions:', error);
        showNotification('Error importing transactions: ' + error.message, 'error');

        // Re-enable button
        const importBtn = document.getElementById('import-foreign-btn');
        importBtn.disabled = false;
        importBtn.textContent = 'Import Verified Transactions';
    }
}
