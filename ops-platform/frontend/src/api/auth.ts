import api from './client'

export interface LoginData {
    username: string
    password: string
}

export interface RegisterData {
    username: string
    email: string
    password: string
    full_name?: string
}

export const authApi = {
    login(data: LoginData) {
        const formData = new FormData()
        formData.append('username', data.username)
        formData.append('password', data.password)
        return api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    register(data: RegisterData) {
        return api.post('/auth/register', data)
    },

    getCurrentUser() {
        return api.get('/auth/me')
    },

    logout() {
        return api.post('/auth/logout')
    }
}
