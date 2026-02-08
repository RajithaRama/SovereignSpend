// Dashboard Component

let timeseriesChart = null;
let categoryChart = null;
let categoryTimeseriesChart = null;

async function loadDashboard() {
    try {
        // Load all dashboard data
        const [summary, categories, timeseries, accountsOverview, recent, categoryTrends] = await Promise.all([
            api.get('/api/dashboard/summary'),
            api.get('/api/dashboard/categories'),
            api.get('/api/dashboard/timeseries'),
            api.get('/api/dashboard/accounts-overview'),
            api.get('/api/dashboard/recent'),
            api.get('/api/dashboard/category-timeseries')
        ]);

        initCategoryFilters();
        renderStats(summary);
        renderTimeseriesChart(timeseries);
        renderCategoryChart(categories);
        renderCategoryTimeseriesChart(categoryTrends);
        renderAccountsOverview(accountsOverview);
        renderRecentTransactions(recent);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function renderStats(summary) {
    const statsGrid = document.getElementById('stats-grid');
    const monthlyNet = summary.monthly_income - summary.monthly_expenses;

    statsGrid.innerHTML = `
        <div class="glass-card stat-card">
            <div class="stat-label">Total Balance</div>
            <div class="stat-value">${formatCurrency(summary.total_balance)}</div>
        </div>
        
        <div class="glass-card stat-card">
            <div class="stat-label">Monthly Income</div>
            <div class="stat-value">${formatCurrency(summary.monthly_income)}</div>
            <div class="stat-change positive">↑ This month</div>
        </div>
        
        <div class="glass-card stat-card">
            <div class="stat-label">Monthly Expenses</div>
            <div class="stat-value">${formatCurrency(summary.monthly_expenses)}</div>
            <div class="stat-change negative">↓ This month</div>
        </div>
        
        <div class="glass-card stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div class="stat-label" style="color: rgba(255,255,255,0.9);">Net This Month</div>
            <div style="font-size: 2rem; font-weight: 700; color: white;">${formatCurrency(monthlyNet)}</div>
            <div style="font-size: 0.875rem; color: rgba(255,255,255,0.8); margin-top: 0.5rem;">
                ${summary.account_count} Active Account${summary.account_count !== 1 ? 's' : ''}
            </div>
        </div>
    `;
}

function renderTimeseriesChart(data) {
    const ctx = document.getElementById('timeseriesChart');

    if (timeseriesChart) {
        timeseriesChart.destroy();
    }

    const labels = data.map(d => d.date);
    const savings = data.map(d => d.savings);
    const earnings = data.map(d => d.earnings);
    const expenditure = data.map(d => d.expenditure);

    timeseriesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Cumulative Savings',
                    data: savings,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Monthly Earnings',
                    data: earnings,
                    borderColor: '#48bb78',
                    backgroundColor: 'rgba(72, 187, 120, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Monthly Expenditure',
                    data: expenditure,
                    borderColor: '#f56565',
                    backgroundColor: 'rgba(245, 101, 101, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#a0aec0',
                        font: { size: 12 }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a0aec0',
                        callback: function (value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a0aec0'
                    }
                }
            }
        }
    });
}

function renderCategoryChart(categories) {
    const container = document.getElementById('category-chart-container');
    const totalDisplay = document.getElementById('category-total-display');

    if (categoryChart) {
        categoryChart.destroy();
        categoryChart = null;
    }

    // Calculate total
    const total = categories.reduce((sum, item) => sum + item.amount, 0);
    if (totalDisplay) {
        totalDisplay.textContent = `Total: ${formatCurrency(total)}`;
    }

    if (categories.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">No expense data available</p>';
        return;
    }

    // Ensure canvas exists
    if (!document.getElementById('categoryChart')) {
        container.innerHTML = '<canvas id="categoryChart"></canvas>';
    }

    const ctx = document.getElementById('categoryChart');

    const labels = categories.map(c => c.category);
    const data = categories.map(c => c.amount);

    // Generate gradient colors
    const colors = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c',
        '#4facfe', '#00f2fe', '#fa709a', '#fee140',
        '#a8edea', '#fed6e3', '#fbc2eb', '#a6c1ee'
    ];

    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#a0aec0',
                        font: { size: 12 },
                        padding: 15,
                        generateLabels: function (chart) {
                            const data = chart.data;
                            return data.labels.map((label, i) => {
                                const value = data.datasets[0].data[i];
                                return {
                                    text: `${label}: $${value.toFixed(2)}`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    hidden: false,
                                    index: i
                                };
                            });
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.chart._metasets[context.datasetIndex].total;
                            const percentage = (value / total * 100).toFixed(1) + '%';
                            return `${label}: ${formatCurrency(value)} (${percentage})`;
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const category = categoryChart.data.labels[index];

                    // Get current filter values
                    const month = document.getElementById('category-month').value;
                    const year = document.getElementById('category-year').value;

                    fetchCategoryTransactions(category, month, year);
                }
            },
            onHover: (event, chartElement) => {
                event.native.target.style.cursor = chartElement[0] ? 'pointer' : 'default';
            }
        }
    });
}

async function fetchCategoryTransactions(category, month, year) {
    const section = document.getElementById('category-details-section');
    const tableContainer = document.getElementById('category-details-table');
    const title = document.getElementById('category-details-title');

    // Show section and loading state
    section.classList.remove('hidden');
    title.textContent = `Transactions: ${category}`;
    tableContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 1rem;">Loading...</p>';

    // Scroll to section
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });

    try {
        let url = `/api/transactions/?category=${encodeURIComponent(category)}`;

        if (month && year) {
            // Construct start and end dates based on month/year
            const startDate = new Date(year, month - 1, 1);
            let endDate;
            if (month == 12) {
                endDate = new Date(parseInt(year) + 1, 0, 1);
            } else {
                endDate = new Date(year, month, 1);
            }

            // Format dates as YYYY-MM-DD for the API
            // API expects ISO strings or YYYY-MM-DD
            url += `&start_date=${startDate.toISOString()}&end_date=${endDate.toISOString()}`;
        } else {
            // Default to last 30 days if no filter selected, matching the default chart view
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(endDate.getDate() - 30);
            url += `&start_date=${startDate.toISOString()}`;
        }

        const transactions = await api.get(url);
        renderCategoryTransactionsTable(transactions, tableContainer);

    } catch (error) {
        console.error('Error fetching details:', error);
        tableContainer.innerHTML = '<p style="text-align: center; color: #f56565;">Error loading transactions</p>';
    }
}

function renderCategoryTransactionsTable(transactions, container) {
    if (transactions.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 1rem;">No transactions found for this period.</p>';
        return;
    }

    container.innerHTML = `
        <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    ${transactions.map(t => `
                        <tr>
                            <td style="color: var(--text-secondary);">${formatDate(t.date)}</td>
                            <td>${t.description || 'No description'}</td>
                            <td style="font-weight: 600; color: #f56565;">
                                -${formatCurrency(t.amount)}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderAccountsOverview(accounts) {
    const container = document.getElementById('accounts-overview');

    if (accounts.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No accounts found. Create an account to get started.</p>';
        return;
    }

    container.innerHTML = accounts.map(acc => {
        const changeClass = acc.monthly_change >= 0 ? 'positive' : 'negative';
        const changeIcon = acc.monthly_change >= 0 ? '↑' : '↓';

        return `
            <div class="glass-card mb-3" style="padding: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4>${acc.account.name}</h4>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            ${formatCurrency(acc.account.balance)}
                        </div>
                        <div class="stat-change ${changeClass}" style="margin: 0;">
                            ${changeIcon} ${formatCurrency(Math.abs(acc.monthly_change))} this month
                        </div>
                    </div>
                </div>
                ${acc.recent_transactions.length > 0 ? `
                    <div style="border-top: 1px solid var(--border-color); padding-top: 1rem;">
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Recent Transactions</div>
                        ${acc.recent_transactions.slice(0, 3).map(t => `
                            <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                                <span style="color: var(--text-secondary);">${t.description || 'Transaction'}</span>
                                <span class="${t.type === 'income' ? 'stat-change positive' : 'stat-change negative'}">
                                    ${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function renderRecentTransactions(transactions) {
    const container = document.getElementById('recent-transactions');

    if (transactions.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No recent transactions</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Type</th>
                    <th>Amount</th>
                </tr>
            </thead>
            <tbody>
                ${transactions.map(t => `
                    <tr>
                        <td style="color: var(--text-secondary);">${formatDate(t.date)}</td>
                        <td>${t.description || 'No description'}</td>
                        <td><span class="badge" style="background: rgba(102, 126, 234, 0.2); color: #667eea;">${t.category || 'Uncategorized'}</span></td>
                        <td><span class="badge badge-${t.type}">${t.type}</span></td>
                        <td style="font-weight: 600; color: ${t.type === 'income' ? '#48bb78' : '#f56565'};">
                            ${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function initCategoryFilters() {
    const monthSelect = document.getElementById('category-month');
    const yearSelect = document.getElementById('category-year');

    // Populate years (current year and previous 4 years)
    const currentYear = new Date().getFullYear();
    for (let i = 0; i < 5; i++) {
        const year = currentYear - i;
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }

    // Add event listeners
    const handleFilterChange = () => {
        const month = monthSelect.value;
        const year = yearSelect.value;
        updateCategoryChart(month, year);
    };

    monthSelect.addEventListener('change', handleFilterChange);
    yearSelect.addEventListener('change', handleFilterChange);
}

async function updateCategoryChart(month, year) {
    try {
        let url = '/api/dashboard/categories';
        if (month && year) {
            url += `?month=${month}&year=${year}`;
        }

        const categories = await api.get(url);
        renderCategoryChart(categories);
    } catch (error) {
        console.error('Error updating category chart:', error);
    }
}

function renderCategoryTimeseriesChart(data) {
    const ctx = document.getElementById('categoryTimeseriesChart');

    if (categoryTimeseriesChart) {
        categoryTimeseriesChart.destroy();
    }

    if (!data || data.length === 0) {
        // Handle empty state
        return;
    }

    const labels = data.map(d => d.date);

    // Extract all unique categories
    const categories = new Set();
    data.forEach(d => {
        Object.keys(d).forEach(key => {
            if (key !== 'date') categories.add(key);
        });
    });

    // Generate datasets
    // Use a fixed set of colors
    const colors = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c',
        '#4facfe', '#00f2fe', '#fa709a', '#fee140'
    ];

    const datasets = Array.from(categories).map((category, index) => {
        const color = colors[index % colors.length];
        return {
            label: category,
            data: data.map(d => d[category] || 0),
            borderColor: color,
            backgroundColor: color, // Legend color
            borderWidth: 2,
            fill: false,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4
        };
    });

    categoryTimeseriesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#a0aec0',
                        usePointStyle: true,
                        boxWidth: 6
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += formatCurrency(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#a0aec0',
                        callback: value => '$' + value.toLocaleString()
                    }
                },
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                }
            }
        }
    });
}
