// Accounts Component

async function loadAccounts() {
    try {
        const accounts = await api.get('/api/accounts/');
        state.accounts = accounts;
        renderAccountsList(accounts);
    } catch (error) {
        console.error('Error loading accounts:', error);
        showNotification('Error loading accounts', 'error');
    }
}

function renderAccountsList(accounts) {
    const container = document.getElementById('accounts-list');

    if (accounts.length === 0) {
        container.innerHTML = '<p style="grid-column: 1/-1; color: var(--text-secondary);">No accounts yet. Create your first account to get started!</p>';
        return;
    }

    container.innerHTML = accounts.map(account => `
        <div class="glass-card stat-card">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                <div class="stat-label">${account.name}</div>
                <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="deleteAccount(${account.id})">Delete</button>
            </div>
            <div class="stat-value">${formatCurrency(account.balance)}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">
                Created ${formatDate(account.created_at)}
            </div>
        </div>
    `).join('');
}

// Add account functionality
document.getElementById('add-account-btn').addEventListener('click', () => {
    document.getElementById('add-account-modal').classList.remove('hidden');
});

document.getElementById('cancel-account-btn').addEventListener('click', () => {
    document.getElementById('add-account-modal').classList.add('hidden');
    document.getElementById('add-account-form').reset();
});

document.getElementById('add-account-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('account-name').value;
    const balance = parseFloat(document.getElementById('account-balance').value);

    try {
        await api.post('/api/accounts/', { name, balance });
        showNotification('Account created successfully!');
        document.getElementById('add-account-modal').classList.add('hidden');
        document.getElementById('add-account-form').reset();
        loadAccounts();
    } catch (error) {
        console.error('Error creating account:', error);
        showNotification('Error creating account', 'error');
    }
});

async function deleteAccount(accountId) {
    if (!confirm('Are you sure you want to delete this account? All associated transactions will be deleted.')) {
        return;
    }

    try {
        await api.delete(`/api/accounts/${accountId}`);
        showNotification('Account deleted successfully');
        loadAccounts();
    } catch (error) {
        console.error('Error deleting account:', error);
        showNotification('Error deleting account', 'error');
    }
}
