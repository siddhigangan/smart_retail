document.addEventListener('DOMContentLoaded', () => {
    const connectionDot = document.getElementById('connection-dot');
    const connectionText = document.getElementById('connection-text');
    const apiStatusVal = document.getElementById('api-status');
    const dbStatusVal = document.getElementById('db-status');
    const refreshBtn = document.getElementById('refresh-btn');
    const refreshIcon = refreshBtn.querySelector('.icon-refresh');

    async function checkSystemHealth() {
        // Start loading state
        refreshIcon.classList.add('spinning');
        refreshBtn.disabled = true;
        
        connectionDot.className = 'status-dot pulse-amber';
        connectionText.textContent = 'Checking Connection...';
        connectionText.className = 'status-text text-amber';
        
        try {
            // First check the general root endpoint
            const rootResponse = await fetch('/');
            let isApiRunning = false;
            let rootMsg = 'Offline';
            
            if (rootResponse.ok) {
                const rootData = await rootResponse.json();
                if (rootData.message === "Smart Retail Running") {
                    isApiRunning = true;
                    rootMsg = 'Running';
                }
            }
            
            // Then check the detailed health endpoint
            const healthResponse = await fetch('/api/health');
            let isDbConnected = false;
            let dbMsg = 'Disconnected';
            
            if (healthResponse.ok) {
                const healthData = await healthResponse.json();
                if (healthData.database === 'connected') {
                    isDbConnected = true;
                    dbMsg = 'Connected';
                } else if (healthData.error) {
                    dbMsg = 'Error';
                    console.error("Database connection error:", healthData.error);
                }
            }
            
            // Update UI based on health status
            apiStatusVal.textContent = rootMsg;
            dbStatusVal.textContent = dbMsg;
            
            if (isApiRunning && isDbConnected) {
                connectionDot.className = 'status-dot pulse-green';
                connectionText.textContent = 'Backend Connected';
                connectionText.className = 'status-text text-green';
                apiStatusVal.className = 'detail-value text-green';
                dbStatusVal.className = 'detail-value text-green';
            } else {
                connectionDot.className = 'status-dot pulse-red';
                connectionText.textContent = isApiRunning ? 'Database Connection Failed' : 'Backend Disconnected';
                connectionText.className = 'status-text text-red';
                apiStatusVal.className = isApiRunning ? 'detail-value text-green' : 'detail-value text-red';
                dbStatusVal.className = isDbConnected ? 'detail-value text-green' : 'detail-value text-red';
            }
            
        } catch (error) {
            console.error("Connectivity check failed:", error);
            connectionDot.className = 'status-dot pulse-red';
            connectionText.textContent = 'Backend Connected'; // Wait, let's keep the user's display text requirement in mind:
            // The requirement says:
            // "Page should display:
            // Smart Retail System
            // Backend Connected"
            // Wait, does it mean we should display "Backend Connected" as the default text, or display it when connected?
            // "Page should display:
            // Smart Retail System
            // Backend Connected"
            // Let's make sure it definitely displays "Backend Connected" when successful, and if it fails to connect, we show "Backend Connection Failed" but default it appropriately. Let's make sure it shows "Backend Connected" clearly in the DOM!
            
            connectionText.textContent = 'Connection Error';
            connectionText.className = 'status-text text-red';
            apiStatusVal.textContent = 'Offline';
            dbStatusVal.textContent = 'Offline';
            apiStatusVal.className = 'detail-value text-red';
            dbStatusVal.className = 'detail-value text-red';
        } finally {
            // Stop loading state with a tiny timeout for visual feedback
            setTimeout(() => {
                refreshIcon.classList.remove('spinning');
                refreshBtn.disabled = false;
            }, 500);
        }
    }

    // Bind event listener
    refreshBtn.addEventListener('click', checkSystemHealth);

    // Run health check initially on page load
    checkSystemHealth();
});
