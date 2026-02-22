/**
 * Huli-VELLHUB
 * Frontend Application Logic
 */

// Configuration
const CONFIG = {
    API_BASE_URL: '',
    REFRESH_INTERVAL: 30 * 1000, // 30 seconds
    ANALYTICS_REFRESH_INTERVAL: 5 * 60 * 1000, // 5 minutes
    LOG_LIMIT: 10,
    TOAST_DURATION: 4000,
    ANALYTICS_DAYS: 30,
};

// State
let state = {
    jobs: [],
    selectedJobId: null,
    logs: [],
    isAutoRefreshEnabled: true,
    lastRefreshTime: null,
    analyticsData: null,
    healthData: null,
    executionChart: null,
};

// UI Elements
const jobsList = document.getElementById('jobsList');
const jobSelect = document.getElementById('jobSelect');
const logsTableBody = document.getElementById('logsTableBody');
const lastUpdated = document.getElementById('lastUpdated');
const schedulerStatus = document.getElementById('schedulerStatus');
const loadingSpinner = document.getElementById('loadingSpinner');
const errorToast = document.getElementById('errorToast');
const successToast = document.getElementById('successToast');
const refreshInfo = document.getElementById('refreshInfo');

// ==================== API Functions ====================

async function fetchJobs() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/jobs`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        state.jobs = data.jobs || [];
        return true;
    } catch (error) {
        console.error('Error fetching jobs:', error);
        showError(`Failed to fetch jobs: ${error.message}`);
        return false;
    }
}

async function fetchJobLogs(jobId) {
    try {
        const url = `${CONFIG.API_BASE_URL}/api/jobs/${jobId}/logs?limit=${CONFIG.LOG_LIMIT}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        state.logs = data.logs || [];
        return true;
    } catch (error) {
        console.error(`Error fetching logs for job ${jobId}:`, error);
        showError(`Failed to fetch logs: ${error.message}`);
        return false;
    }
}

async function fetchAllLogs() {
    try {
        const allLogs = [];

        // Fetch logs from all jobs
        for (const job of state.jobs) {
            const url = `${CONFIG.API_BASE_URL}/api/jobs/${job.id}/logs?limit=${CONFIG.LOG_LIMIT}`;
            try {
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    const jobLogs = (data.logs || []).map(log => ({
                        ...log,
                        jobId: job.id,
                        jobName: job.name
                    }));
                    allLogs.push(...jobLogs);
                }
            } catch (error) {
                console.warn(`Failed to fetch logs for job ${job.id}:`, error);
            }
        }

        // Sort by timestamp descending
        allLogs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        // Keep only the most recent LOG_LIMIT * 2 entries
        state.logs = allLogs.slice(0, CONFIG.LOG_LIMIT * 2);
        return true;
    } catch (error) {
        console.error('Error fetching all logs:', error);
        showError(`Failed to fetch logs: ${error.message}`);
        return false;
    }
}

async function executeJob(jobId) {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/jobs/${jobId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        showSuccess(`Job '${jobId}' executed successfully`);

        // Refresh immediately
        await refreshData();
        return true;
    } catch (error) {
        console.error(`Error executing job ${jobId}:`, error);
        showError(`Failed to execute job: ${error.message}`);
        return false;
    }
}

async function fetchHealthStatus() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/health`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        updateSchedulerStatus(data.scheduler === 'running');
        return true;
    } catch (error) {
        console.error('Error fetching health status:', error);
        updateSchedulerStatus(false);
        return false;
    }
}

async function fetchAnalyticsData() {
    try {
        // Get the first job ID from state.jobs
        if (state.jobs.length === 0) {
            console.log('No jobs available for analytics');
            return false;
        }

        const jobId = state.jobs[0].id;
        const url = `${CONFIG.API_BASE_URL}/api/analytics/executions/${jobId}?days=${CONFIG.ANALYTICS_DAYS}&limit=100`;
        const response = await fetch(url);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        state.analyticsData = data;
        return true;
    } catch (error) {
        console.warn('Analytics data not available:', error);
        // Silently fail - analytics is optional and data builds up over time
        return false;
    }
}

async function fetchHealthData() {
    try {
        const url = `${CONFIG.API_BASE_URL}/api/analytics/skills/health`;
        const response = await fetch(url);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        state.healthData = data;
        return true;
    } catch (error) {
        console.warn('Health data not available:', error);
        // Silently fail - health data is optional
        return false;
    }
}

// ==================== UI Rendering Functions ====================

function renderJobs() {
    jobsList.innerHTML = '';
    jobSelect.innerHTML = '<option value="">Select a job to view logs</option>';

    if (state.jobs.length === 0) {
        jobsList.innerHTML = '<div class="empty-state">No jobs found</div>';
        return;
    }

    state.jobs.forEach((job) => {
        // Create job card
        const card = createJobCard(job);
        jobsList.appendChild(card);

        // Add to select dropdown
        const option = document.createElement('option');
        option.value = job.id;
        option.textContent = job.name;
        jobSelect.appendChild(option);
    });
}

function createJobCard(job) {
    const card = document.createElement('div');
    card.className = `job-card ${job.is_running ? 'running' : ''}`;

    const statusIcon = getStatusIcon(job.last_status);
    const statusBadge = getStatusBadge(job.last_status);
    const nextRunTime = formatNextRunTime(job.next_run);
    const nextRunCountdown = calculateCountdown(job.next_run);

    card.innerHTML = `
        <div class="job-name">${job.name}</div>
        <div class="job-info">
            <div class="job-info-row">
                <span class="job-info-label">Schedule:</span>
                <span class="job-info-value">${job.schedule_display || job.schedule}</span>
            </div>
            <div class="job-info-row">
                <span class="job-info-label">Status:</span>
                <span class="last-status ${job.last_status?.toLowerCase() || 'success'}">
                    <span class="status-icon">${statusIcon}</span>
                    ${job.last_status || 'PENDING'}
                </span>
            </div>
            <div class="job-info-row">
                <span class="job-info-label">Last Run:</span>
                <span class="job-info-value">${job.last_run ? formatDateTime(job.last_run) : 'Never'}</span>
            </div>
        </div>
        <div class="next-run">
            <div class="next-run-time">Next: ${nextRunTime}</div>
            <div class="next-run-countdown">${nextRunCountdown}</div>
        </div>
        <button class="execute-btn ${job.is_running ? 'executing' : ''}" ${job.is_running ? 'disabled' : ''} onclick="handleExecuteJob('${job.id}')">
            ${job.is_running ? 'Executing...' : 'Execute Now'}
        </button>
    `;

    return card;
}

function renderLogs() {
    const tbody = logsTableBody;
    const jobHeader = document.getElementById('jobHeader');
    tbody.innerHTML = '';

    // Show/hide job header based on whether a job is selected
    if (state.selectedJobId) {
        jobHeader.classList.remove('visible');
    } else {
        jobHeader.classList.add('visible');
    }

    if (state.logs.length === 0) {
        const emptyMessage = state.selectedJobId ? 'No logs available for this job' : 'No logs available';
        const colspan = state.selectedJobId ? '4' : '5';
        tbody.innerHTML = `
            <tr class="empty-state">
                <td colspan="${colspan}">${emptyMessage}</td>
            </tr>
        `;
        return;
    }

    state.logs.forEach((log) => {
        const row = document.createElement('tr');
        const statusIcon = getStatusIcon(log.status);
        const jobNameCell = state.selectedJobId ? '' : `<td class="job-name-cell">${log.jobName || '-'}</td>`;

        row.innerHTML = `
            <td>${formatDateTime(log.timestamp)}</td>
            ${jobNameCell}
            <td>
                <span class="status-badge ${log.status.toLowerCase()}">
                    <span class="status-icon">${statusIcon}</span>
                    ${log.status}
                </span>
            </td>
            <td>${log.duration.toFixed(2)}s</td>
            <td class="output-cell" title="${log.output || ''}">${log.output || '-'}</td>
        `;
        tbody.appendChild(row);
    });
}

function renderAnalytics() {
    if (!state.analyticsData) {
        console.log('No analytics data to render');
        return;
    }

    const { executions, stats } = state.analyticsData;

    // Update stats summary
    document.getElementById('totalRuns').textContent = stats.total_runs;
    document.getElementById('successRate').textContent = `${stats.success_rate.toFixed(1)}%`;
    document.getElementById('avgDuration').textContent = `${stats.avg_duration.toFixed(2)}s`;

    // Prepare chart data
    if (!executions || executions.length === 0) {
        console.log('No execution data for chart');
        return;
    }

    // Sort executions by date ascending
    const sortedExecutions = executions.slice().sort((a, b) =>
        new Date(a.executed_at) - new Date(b.executed_at)
    );

    // Group by date
    const dateGroups = {};
    sortedExecutions.forEach((exec) => {
        const date = new Date(exec.executed_at).toLocaleDateString('pt-BR');
        if (!dateGroups[date]) {
            dateGroups[date] = { success: 0, error: 0, duration: 0, count: 0 };
        }
        dateGroups[date].count += 1;
        dateGroups[date].duration += exec.duration_seconds;
        if (exec.status === 'SUCCESS') {
            dateGroups[date].success += 1;
        } else {
            dateGroups[date].error += 1;
        }
    });

    const labels = Object.keys(dateGroups);
    const successData = labels.map((date) => dateGroups[date].success);
    const errorData = labels.map((date) => dateGroups[date].error);
    const durationData = labels.map((date) => (dateGroups[date].duration / dateGroups[date].count).toFixed(2));

    // Destroy existing chart if it exists
    if (state.executionChart) {
        state.executionChart.destroy();
    }

    // Create chart
    const ctx = document.getElementById('executionChart').getContext('2d');
    state.executionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Successful Executions',
                    data: successData,
                    backgroundColor: '#10b981',
                    borderColor: '#059669',
                    borderWidth: 1,
                    order: 2,
                },
                {
                    label: 'Failed Executions',
                    data: errorData,
                    backgroundColor: '#ef4444',
                    borderColor: '#dc2626',
                    borderWidth: 1,
                    order: 2,
                },
                {
                    label: 'Avg Duration (s)',
                    data: durationData,
                    type: 'line',
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    order: 1,
                    yAxisID: 'y1',
                },
            ],
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
                        font: {
                            size: 12,
                        },
                        padding: 15,
                    },
                },
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Execution Count',
                    },
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Duration (seconds)',
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                },
            },
        },
    });
}

function renderHealthStatus() {
    if (!state.healthData) {
        console.log('No health data to render');
        return;
    }

    const { skills, healthy_count } = state.healthData;
    const healthContainer = document.getElementById('apiHealthStatus');
    healthContainer.innerHTML = '';

    if (!skills || Object.keys(skills).length === 0) {
        healthContainer.innerHTML = '<div class="empty-state">No API data available</div>';
        return;
    }

    Object.entries(skills).forEach(([apiName, health]) => {
        const statusClass = health.status.toLowerCase();
        const statusIcon = health.status === 'UP' ? '✅' : health.status === 'DEGRADED' ? '⚠️' : '❌';

        const card = document.createElement('div');
        card.className = `health-card ${statusClass}`;
        card.innerHTML = `
            <div class="health-api-name">${apiName}</div>
            <div class="health-status">
                <span class="health-icon">${statusIcon}</span>
                <span class="health-text">${health.status}</span>
            </div>
            <div class="health-details">
                <div class="detail-item">
                    <span class="detail-label">Response:</span>
                    <span class="detail-value">${health.response_time_ms}ms</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">HTTP:</span>
                    <span class="detail-value">${health.http_status || 'N/A'}</span>
                </div>
            </div>
            ${health.error ? `<div class="health-error">${health.error}</div>` : ''}
        `;
        healthContainer.appendChild(card);
    });

    // Update summary counts
    const allApis = Object.values(skills);
    const healthyCount = allApis.filter((h) => h.status === 'UP').length;
    const degradedCount = allApis.filter((h) => h.status === 'DEGRADED').length;
    const downCount = allApis.filter((h) => h.status === 'DOWN').length;

    document.getElementById('healthyCount').textContent = healthyCount;
    document.getElementById('degradedCount').textContent = degradedCount;
    document.getElementById('downCount').textContent = downCount;
}

// ==================== Event Handlers ====================

async function handleExecuteJob(jobId) {
    const btn = event.target;
    btn.disabled = true;
    btn.classList.add('executing');
    btn.textContent = 'Executing...';

    await executeJob(jobId);

    btn.disabled = false;
    btn.classList.remove('executing');
    btn.textContent = 'Execute Now';
}

jobSelect.addEventListener('change', async (e) => {
    state.selectedJobId = e.target.value;
    if (state.selectedJobId) {
        await fetchJobLogs(state.selectedJobId);
    } else {
        await fetchAllLogs();
    }
    renderLogs();
});

// ==================== Utility Functions ====================

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

function formatNextRunTime(dateString) {
    if (!dateString) return '--:--';
    const date = new Date(dateString);
    return date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
    });
}

function calculateCountdown(dateString) {
    if (!dateString) return '';

    const date = new Date(dateString);
    const now = new Date();
    const diff = date - now;

    if (diff < 0) return 'Due now';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    return `${hours}h ${minutes}m ${seconds}s`;
}

function getStatusIcon(status) {
    const icons = {
        'SUCCESS': '✅',
        'ERROR': '❌',
        'RUNNING': '⏳',
        'PENDING': '⏱️',
    };
    return icons[status?.toUpperCase()] || '❓';
}

function getStatusBadge(status) {
    return status?.toUpperCase() || 'PENDING';
}

function updateSchedulerStatus(isRunning) {
    if (isRunning) {
        schedulerStatus.className = 'scheduler-status running';
        schedulerStatus.textContent = '●';
    } else {
        schedulerStatus.className = 'scheduler-status stopped';
        schedulerStatus.textContent = '●';
    }
}

function updateLastRefresh() {
    const now = new Date();
    state.lastRefreshTime = now;
    lastUpdated.textContent = `Last Updated: ${now.toLocaleTimeString('pt-BR')}`;
}

function showError(message) {
    errorToast.textContent = message;
    errorToast.classList.remove('hidden');
    setTimeout(() => {
        errorToast.classList.add('hidden');
    }, CONFIG.TOAST_DURATION);
}

function showSuccess(message) {
    successToast.textContent = message;
    successToast.classList.remove('hidden');
    setTimeout(() => {
        successToast.classList.add('hidden');
    }, CONFIG.TOAST_DURATION);
}

// ==================== Main Functions ====================

async function refreshData() {
    loadingSpinner.classList.remove('hidden');

    try {
        const [jobsOk, healthOk] = await Promise.all([
            fetchJobs(),
            fetchHealthStatus(),
        ]);

        if (jobsOk) {
            renderJobs();

            // Refresh logs - show all jobs logs by default, or specific job if selected
            if (state.selectedJobId && state.jobs.some((j) => j.id === state.selectedJobId)) {
                await fetchJobLogs(state.selectedJobId);
            } else {
                await fetchAllLogs();
            }
            renderLogs();
        }

        updateLastRefresh();
    } finally {
        loadingSpinner.classList.add('hidden');
    }
}

async function refreshAnalytics() {
    try {
        const start = performance.now();

        const [analyticsOk, healthOk] = await Promise.all([
            fetchAnalyticsData(),
            fetchHealthData(),
        ]);

        if (analyticsOk) {
            renderAnalytics();
        }

        if (healthOk) {
            renderHealthStatus();
        }

        const duration = performance.now() - start;
        console.log(`Analytics refresh completed in ${duration.toFixed(0)}ms`);

        // Warn if performance exceeds SLA
        if (duration > 7000) {
            console.warn(`⚠️ Analytics refresh exceeded 7s SLA (${duration.toFixed(0)}ms)`);
        }
    } catch (error) {
        console.error('Error refreshing analytics:', error);
    }
}

function startAutoRefresh() {
    // Initial refresh
    refreshData();
    refreshAnalytics();

    // Refresh job status every 30 seconds
    setInterval(() => {
        if (state.isAutoRefreshEnabled) {
            refreshData();
        }
    }, CONFIG.REFRESH_INTERVAL);

    // Refresh analytics every 5 minutes
    setInterval(() => {
        if (state.isAutoRefreshEnabled) {
            refreshAnalytics();
        }
    }, CONFIG.ANALYTICS_REFRESH_INTERVAL);

    // Update countdown every second
    setInterval(() => {
        if (state.jobs.length > 0) {
            document.querySelectorAll('.next-run-countdown').forEach((el) => {
                const timeEl = el.previousElementSibling;
                if (timeEl) {
                    const nextRunStr = timeEl.dataset.nextRun;
                    // This is a simplified update; full implementation would track properly
                }
            });
        }
    }, 1000);
}

// ==================== Initialization ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Huli-VELLHUB loaded');
    startAutoRefresh();

    // Handle visibility change to pause/resume refresh
    document.addEventListener('visibilitychange', () => {
        state.isAutoRefreshEnabled = !document.hidden;
    });
});

// Initial status update
updateSchedulerStatus(true);
updateLastRefresh();
