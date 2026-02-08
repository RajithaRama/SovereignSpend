// Transactions Component

let editingTransactionId = null;
let currentPage = 1;
const transactionsPerPage = 20;

async function loadTransactions() {
    try {
        const [transactions, accounts] = await Promise.all([
            api.get('/api/transactions/'),
            api.get('/api/accounts/')
        ]);

        state.transactions = transactions;
        state.accounts = accounts;

        currentPage = 1; // Reset to first page
        renderTransactionsTable(transactions);
        populateAccountFilter();
        populateCategoryFilter(transactions);
    } catch (error) {
        console.error('Error loading transactions:', error);
        showNotification('Error loading transactions', 'error');
    }
}

function renderTransactionsTable(transactions) {
    const container = document.getElementById('transactions-table-container');
    const paginationContainer = document.getElementById('pagination-controls');

    if (transactions.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">No transactions yet</p>';
        paginationContainer.innerHTML = '';
        return;
    }

    // Get account name lookup
    const accountLookup = {};
    state.accounts.forEach(acc => {
        accountLookup[acc.id] = acc.name;
    });

    // Calculate pagination
    const totalPages = Math.ceil(transactions.length / transactionsPerPage);
    const startIndex = (currentPage - 1) * transactionsPerPage;
    const endIndex = startIndex + transactionsPerPage;
    const paginatedTransactions = transactions.slice(startIndex, endIndex);

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Account</th>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Type</th>
                    <th>Amount</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${paginatedTransactions.map(t => {
        const isEditing = editingTransactionId === t.id;
        if (isEditing) {
            return renderEditRow(t);
        }
        return `
                    <tr>
                        <td style="color: var(--text-secondary);">${formatDate(t.date)}</td>
                        <td>${accountLookup[t.account_id] || 'Unknown'}</td>
                        <td>${t.description || 'No description'}</td>
                        <td><span class="badge" style="background: rgba(102, 126, 234, 0.2); color: #667eea;">${t.category || 'Uncategorized'}</span></td>
                        <td><span class="badge badge-${t.type}">${t.type}</span></td>
                        <td style="font-weight: 600; color: ${t.type === 'income' ? '#48bb78' : '#f56565'};">
                            ${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
                        </td>
                        <td>
                            <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; margin-right: 0.5rem;" onclick="editTransaction(${t.id})">Edit</button>
                            <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="deleteTransaction(${t.id})">Delete</button>
                        </td>
                    </tr>
                    `;
    }).join('')}
            </tbody>
        </table>
    `;

    // Render pagination controls
    if (totalPages > 1) {
        paginationContainer.innerHTML = `
            <div style="color: var(--text-secondary); font-size: 0.875rem;">
                Showing ${startIndex + 1}-${Math.min(endIndex, transactions.length)} of ${transactions.length} transactions
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
                <button 
                    class="btn btn-secondary" 
                    style="padding: 0.5rem 0.75rem; font-size: 0.875rem;" 
                    onclick="changePage(${currentPage - 1})"
                    ${currentPage === 1 ? 'disabled' : ''}
                >
                    ← Previous
                </button>
                <span style="color: var(--text-secondary); font-size: 0.875rem;">
                    Page ${currentPage} of ${totalPages}
                </span>
                <button 
                    class="btn btn-secondary" 
                    style="padding: 0.5rem 0.75rem; font-size: 0.875rem;" 
                    onclick="changePage(${currentPage + 1})"
                    ${currentPage === totalPages ? 'disabled' : ''}
                >
                    Next →
                </button>
            </div>
        `;
    } else {
        paginationContainer.innerHTML = '';
    }
}

function changePage(newPage) {
    currentPage = newPage;
    renderTransactionsTable(state.transactions);
}

function renderEditRow(t) {
    return `
    <tr class="editing-row">
        <td><input type="datetime-local" id="edit-date-${t.id}" value="${t.date ? t.date.slice(0, 16) : ''}" style="width: 140px;"></td>
        <td>
            <select id="edit-account-${t.id}" style="width: 120px;">
                ${state.accounts.map(acc => `<option value="${acc.id}" ${acc.id === t.account_id ? 'selected' : ''}>${acc.name}</option>`).join('')}
            </select>
        </td>
        <td><input type="text" id="edit-desc-${t.id}" value="${t.description || ''}"></td>
        <td><input type="text" id="edit-category-${t.id}" value="${t.category || ''}" style="width: 120px;"></td>
        <td>
            <select id="edit-type-${t.id}" style="width: 100px;">
                <option value="income" ${t.type === 'income' ? 'selected' : ''}>Income</option>
                <option value="expense" ${t.type === 'expense' ? 'selected' : ''}>Expense</option>
            </select>
        </td>
        <td><input type="number" id="edit-amount-${t.id}" value="${t.amount}" step="0.01" style="width: 100px;"></td>
        <td>
            <button class="btn btn-primary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; margin-right: 0.5rem;" onclick="saveTransaction(${t.id})">Save</button>
            <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="cancelEdit()">Cancel</button>
        </td>
    </tr>
    `;
}

function editTransaction(id) {
    editingTransactionId = id;
    renderTransactionsTable(state.transactions);
}

function cancelEdit() {
    editingTransactionId = null;
    renderTransactionsTable(state.transactions);
}

async function saveTransaction(id) {
    const data = {
        date: document.getElementById(`edit-date-${id}`).value,
        account_id: parseInt(document.getElementById(`edit-account-${id}`).value),
        description: document.getElementById(`edit-desc-${id}`).value,
        category: document.getElementById(`edit-category-${id}`).value,
        type: document.getElementById(`edit-type-${id}`).value,
        amount: parseFloat(document.getElementById(`edit-amount-${id}`).value)
    };

    try {
        await api.put(`/api/transactions/${id}`, data);
        showNotification('Transaction updated successfully');
        editingTransactionId = null;
        loadTransactions(); // Reload to reflect changes and re-sort if needed
    } catch (error) {
        console.error('Error updating transaction:', error);
        showNotification('Error updating transaction', 'error');
    }
}

function populateAccountFilter() {
    const select = document.getElementById('filter-account');
    select.innerHTML = '<option value="">All Accounts</option>' +
        state.accounts.map(acc => `<option value="${acc.id}">${acc.name}</option>`).join('');

    select.addEventListener('change', filterTransactions);
}

function populateCategoryFilter(transactions) {
    const categories = [...new Set(transactions.map(t => t.category).filter(c => c))];
    const select = document.getElementById('filter-category');
    select.innerHTML = '<option value="">All Categories</option>' +
        categories.map(cat => `<option value="${cat}">${cat}</option>`).join('');

    select.addEventListener('change', filterTransactions);
}

async function filterTransactions() {
    const accountId = document.getElementById('filter-account').value;
    const category = document.getElementById('filter-category').value;

    let endpoint = '/api/transactions/?';
    if (accountId) endpoint += `account_id=${accountId}&`;
    if (category) endpoint += `category=${category}&`;

    try {
        const transactions = await api.get(endpoint);
        state.transactions = transactions; // Update state
        currentPage = 1; // Reset to first page when filtering
        renderTransactionsTable(transactions);
    } catch (error) {
        console.error('Error filtering transactions:', error);
    }
}

// Add transaction functionality
document.getElementById('add-transaction-btn').addEventListener('click', () => {
    showAddTransactionModal();
});

function showAddTransactionModal() {
    const modal = `
        <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1000; display: flex; align-items: center; justify-content: center;" id="transaction-modal">
            <div class="glass-card" style="max-width: 500px; width: 100%; margin: 2rem;">
                <h3 class="mb-3">Add Transaction</h3>
                <form id="transaction-form">
                    <div class="form-group">
                        <label>Date</label>
                        <input type="datetime-local" id="trans-date" required>
                    </div>
                    <div class="form-group">
                        <label>Account</label>
                        <select id="trans-account" required>
                            <option value="">Select Account</option>
                            ${state.accounts.map(acc => `<option value="${acc.id}">${acc.name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Amount</label>
                        <input type="number" id="trans-amount" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Type</label>
                        <select id="trans-type" required>
                            <option value="income">Income</option>
                            <option value="expense">Expense</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <input type="text" id="trans-description">
                    </div>
                    <div class="form-group">
                        <label>Category (leave empty for AI classification)</label>
                        <input type="text" id="trans-category">
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <button type="submit" class="btn btn-primary">Add Transaction</button>
                        <button type="button" class="btn btn-secondary" onclick="closeTransactionModal()">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modal);

    // Set default date to now
    const now = new Date();
    // Adjust to local ISO string for datetime-local input
    const localIso = new Date(now.getTime() - (now.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
    document.getElementById('trans-date').value = localIso;

    document.getElementById('transaction-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = {
            date: document.getElementById('trans-date').value,
            account_id: parseInt(document.getElementById('trans-account').value),
            amount: parseFloat(document.getElementById('trans-amount').value),
            type: document.getElementById('trans-type').value,
            description: document.getElementById('trans-description').value || null,
            category: document.getElementById('trans-category').value || null
        };

        // Check for duplicates
        try {
            const duplicates = await api.post('/api/transactions/check-duplicates', data);

            if (duplicates && duplicates.length > 0) {
                // Show duplicate warning
                const confirmed = await showDuplicateWarning(duplicates[0]);
                if (!confirmed) return;
            }

            await api.post('/api/transactions/', data);
            showNotification('Transaction added successfully!');
            closeTransactionModal();
            loadTransactions();
        } catch (error) {
            console.error('Error adding transaction:', error);
            showNotification('Error adding transaction', 'error');
        }
    });
}

function showDuplicateWarning(duplicate) {
    return new Promise((resolve) => {
        const modal = `
            <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 1001; display: flex; align-items: center; justify-content: center;" id="duplicate-warning-modal">
                <div class="glass-card" style="max-width: 450px; width: 100%; margin: 2rem; border: 1px solid #f56565;">
                    <h3 class="mb-3" style="color: #f56565;">⚠️ Potential Duplicate</h3>
                    <p class="mb-3">A similar transaction already exists:</p>
                    <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                            <span style="color:var(--text-secondary)">Date:</span>
                            <span>${formatDate(duplicate.date)}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                            <span style="color:var(--text-secondary)">Description:</span>
                            <span>${duplicate.description}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span style="color:var(--text-secondary)">Amount:</span>
                            <span style="font-weight:600">${formatCurrency(duplicate.amount)}</span>
                        </div>
                    </div>
                    <p class="mb-4">Do you want to add this transaction anyway?</p>
                    <div style="display: flex; gap: 1rem; justify-content: flex-end;">
                        <button class="btn btn-secondary" onclick="closeDuplicateWarning(false)">Cancel</button>
                        <button class="btn btn-primary" onclick="closeDuplicateWarning(true)">Proceed Anyway</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modal);

        window.closeDuplicateWarning = (proceed) => {
            document.getElementById('duplicate-warning-modal').remove();
            delete window.closeDuplicateWarning;
            resolve(proceed);
        };
    });
}

function closeTransactionModal() {
    document.getElementById('transaction-modal')?.remove();
}

// Add transfer functionality
document.getElementById('add-transfer-btn').addEventListener('click', () => {
    showAddTransferModal();
});

// Run Rules functionality
document.getElementById('run-rules-btn').addEventListener('click', async () => {
    try {
        const btn = document.getElementById('run-rules-btn');
        const originalText = btn.textContent;
        btn.textContent = 'Running...';
        btn.disabled = true;

        const result = await api.post('/api/transactions/apply-rules');

        showNotification(`Rules applied! Created ${result.created} new transaction(s).`);
        loadTransactions();

        btn.textContent = originalText;
        btn.disabled = false;
    } catch (error) {
        console.error('Error applying rules:', error);
        showNotification('Error applying rules', 'error');
        document.getElementById('run-rules-btn').textContent = '⚡ Run Rules';
        document.getElementById('run-rules-btn').disabled = false;
    }
});

function showAddTransferModal() {
    const modal = `
        <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1000; display: flex; align-items: center; justify-content: center;" id="transfer-modal">
            <div class="glass-card" style="max-width: 500px; width: 100%; margin: 2rem;">
                <h3 class="mb-3">Transfer Between Accounts</h3>
                <form id="transfer-form">
                    <div class="form-group">
                        <label>From Account</label>
                        <select id="transfer-from" required>
                            <option value="">Select Account</option>
                            ${state.accounts.map(acc => `<option value="${acc.id}">${acc.name} (${formatCurrency(acc.balance)})</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>To Account</label>
                        <select id="transfer-to" required>
                            <option value="">Select Account</option>
                            ${state.accounts.map(acc => `<option value="${acc.id}">${acc.name} (${formatCurrency(acc.balance)})</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Amount</label>
                        <input type="number" id="transfer-amount" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Description (optional)</label>
                        <input type="text" id="transfer-description">
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <button type="submit" class="btn btn-primary">Transfer</button>
                        <button type="button" class="btn btn-secondary" onclick="closeTransferModal()">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modal);

    document.getElementById('transfer-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = {
            from_account_id: parseInt(document.getElementById('transfer-from').value),
            to_account_id: parseInt(document.getElementById('transfer-to').value),
            amount: parseFloat(document.getElementById('transfer-amount').value),
            description: document.getElementById('transfer-description').value || null
        };

        try {
            await api.post('/api/transactions/transfer', data);
            showNotification('Transfer completed successfully!');
            closeTransferModal();
            loadTransactions();
        } catch (error) {
            console.error('Error creating transfer:', error);
            showNotification('Error creating transfer', 'error');
        }
    });
}

function closeTransferModal() {
    document.getElementById('transfer-modal')?.remove();
}

async function deleteTransaction(transactionId) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }

    try {
        await api.delete(`/api/transactions/${transactionId}`);
        showNotification('Transaction deleted successfully');
        loadTransactions();
    } catch (error) {
        console.error('Error deleting transaction:', error);
        showNotification('Error deleting transaction', 'error');
    }
}
