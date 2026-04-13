import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ViewPreferences {
  hiddenColumns: string[]
  hiddenSections: string[]
  density: 'compact' | 'comfortable'
}

interface UserPreferencesState {
  pages: Record<string, ViewPreferences>
  
  // Actions
  setPagePreference: (page: string, prefs: Partial<ViewPreferences>) => void
  toggleColumn: (page: string, columnId: string) => void
  toggleSection: (page: string, sectionId: string) => void
  setDensity: (page: string, density: 'compact' | 'comfortable') => void
}

const DEFAULT_PREFS: ViewPreferences = {
  hiddenColumns: [],
  hiddenSections: [],
  density: 'comfortable',
}

export const useUserPreferences = create<UserPreferencesState>()(
  persist(
    (set, get) => ({
      pages: {},

      setPagePreference: (page, prefs) => {
        set((state) => ({
          pages: {
            ...state.pages,
            [page]: {
              ...(state.pages[page] || DEFAULT_PREFS),
              ...prefs,
            },
          },
        }))
      },

      toggleColumn: (page, columnId) => {
        const current = get().pages[page] || DEFAULT_PREFS
        const isHidden = current.hiddenColumns.includes(columnId)
        const nextHidden = isHidden
          ? current.hiddenColumns.filter((id) => id !== columnId)
          : [...current.hiddenColumns, columnId]
        
        get().setPagePreference(page, { hiddenColumns: nextHidden })
      },

      toggleSection: (page, sectionId) => {
        const current = get().pages[page] || DEFAULT_PREFS
        const isHidden = current.hiddenSections.includes(sectionId)
        const nextHidden = isHidden
          ? current.hiddenSections.filter((id) => id !== sectionId)
          : [...current.hiddenSections, sectionId]
        
        get().setPagePreference(page, { hiddenSections: nextHidden })
      },

      setDensity: (page, density) => {
        get().setPagePreference(page, { density })
      },
    }),
    {
      name: 'user-view-preferences',
    }
  )
)
