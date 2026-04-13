import { create } from 'zustand'

export type DrawerType =
  | 'job' | 'candidate' | 'application' | 'interview'
  | 'agency' | 'agency_job' | 'agency_submission' | 'agency_client'
  | 'candidate_job' | 'candidate_application'
  | 'message_thread' | 'document' | 'offer'

interface DrawerState {
  quickViewOpen: boolean
  quickViewType: DrawerType | null
  quickViewData: any
  fullViewOpen: boolean
  fullViewType: DrawerType | null
  fullViewData: any
  openQuickView: (type: DrawerType, data: any) => void
  openFullView: (type?: DrawerType, data?: any) => void
  closeQuickView: () => void
  closeFullView: () => void
}

export const useDrawerStore = create<DrawerState>((set) => ({
  quickViewOpen: false,
  quickViewType: null,
  quickViewData: null,
  fullViewOpen: false,
  fullViewType: null,
  fullViewData: null,
  openQuickView: (type, data) => set({ quickViewOpen: true, quickViewType: type, quickViewData: data, fullViewOpen: false }),
  openFullView: (type?, data?) => set((state) => ({
    fullViewOpen: true,
    fullViewType: type ?? state.quickViewType,
    fullViewData: data ?? state.quickViewData,
  })),
  closeQuickView: () => set({ quickViewOpen: false, quickViewType: null, quickViewData: null, fullViewOpen: false }),
  closeFullView: () => set({ fullViewOpen: false }),
}))
