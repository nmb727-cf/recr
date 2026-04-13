import http from '@/utils/http'

export const workspaceApi = {
  getSummary: () => http.get('/workspace/summary/'),
  getTasks: () => http.get('/workspace/tasks/'),
  getActivity: () => http.get('/workspace/activity/'),
  getAlerts: () => http.get('/workspace/alerts/'),
  getAI: () => http.get('/workspace/ai/'),
  performTaskAction: (taskId: string, action: 'complete' | 'snooze', days?: number) => 
    http.post(`/workspace/tasks/${taskId}/action/`, { action, days }),
}
