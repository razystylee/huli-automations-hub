/**
 * Huli Automations Hub - Mission Control
 * Frontend Application Logic
 */

// Configuration
const CONFIG = {
    API_BASE_URL: '',
    REFRESH_INTERVAL: 30 * 1000, // 30 seconds
    LOG_LIMIT: 10,
    TOAST_DURATION: 4000,
};

// State
let state = {
    jobs: [],
    selectedJobId: null,
    logs: [],
    isAutoRefreshEnabled: true,
    lastRefreshTime: null,
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
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/health`);
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
                <span class="job-info-value">${job.schedule}</span>
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
    tbody.innerHTML = '';

    if (state.logs.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-state">
                <td colspan="4">No logs available for this job</td>
            </tr>
        `;
        return;
    }

    state.logs.forEach((log) => {
        const row = document.createElement('tr');
        const statusIcon = getStatusIcon(log.status);

        row.innerHTML = `
            <td>${formatDateTime(log.timestamp)}</td>
            <td>
                <span class="status-badge ${log.status.toLowerCase()}">
                    <span class="status-icon">${statusIcon}</span>
                    ${log.status}
                </span>
            </td>
            <td>${log.duration.toFixed(2)}</td>
            <td class="output-cell" title="${log.output || ''}">${log.output || '-'}</td>
        `;
        tbody.appendChild(row);
    });
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
        renderLogs();
    } else {
        state.logs = [];
        renderLogs();
    }
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

            // Refresh logs if a job is selected
            if (state.selectedJobId && state.jobs.some((j) => j.id === state.selectedJobId)) {
                await fetchJobLogs(state.selectedJobId);
                renderLogs();
            }
        }

        updateLastRefresh();
    } finally {
        loadingSpinner.classList.add('hidden');
    }
}

function startAutoRefresh() {
    // Initial refresh
    refreshData();

    // Refresh every N seconds
    setInterval(() => {
        if (state.isAutoRefreshEnabled) {
            refreshData();
        }
    }, CONFIG.REFRESH_INTERVAL);

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
    console.log('Huli Automations Hub - Mission Control loaded');
    startAutoRefresh();

    // Handle visibility change to pause/resume refresh
    document.addEventListener('visibilitychange', () => {
        state.isAutoRefreshEnabled = !document.hidden;
    });
});

// Initial status update
updateSchedulerStatus(true);
updateLastRefresh();
