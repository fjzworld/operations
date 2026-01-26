import api from './client'

export const monitoringApi = {
    getDashboard() {
        return api.get('/monitoring/dashboard')
    },

    updateMetrics() {
        return api.get('/monitoring/metrics/update')
    }
}
