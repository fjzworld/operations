import api from './client'

export const resourceApi = {
    list(params?: any) {
        return api.get('/resources', { params })
    },

    get(id: number) {
        return api.get(`/resources/${id}`)
    },

    create(data: any) {
        return api.post('/resources', data)
    },

    update(id: number, data: any) {
        return api.put(`/resources/${id}`, data)
    },

    delete(id: number) {
        return api.delete(`/resources/${id}`)
    },

    updateMetrics(id: number, metrics: any) {
        return api.post(`/resources/${id}/metrics`, metrics)
    },

    getStats() {
        return api.get('/resources/stats/summary')
    }
}
