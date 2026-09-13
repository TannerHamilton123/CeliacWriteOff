import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

const API_URL = import.meta.env.VITE_API_URL

export interface LineItem {
  item_name: string | null
  item_quantity: number | null
  item_price: number | null
  is_gluten_substitute: boolean
}

export type ItemSource = 'file' | 'manual'
export type ItemStatus = 'pending' | 'extracted' | 'failed' | 'verified'

export interface Item {
  id: string
  source: ItemSource
  status: ItemStatus
  name: string
  notes: string
  original_filename: string | null
  merchant_name: string | null
  merchant_address: string | null
  transaction_date: string | null
  transaction_time: string | null
  total_amount: number | null
  line_items: LineItem[]
  error_message: string | null
  created_at: string
  updated_at: string
  verified_at: string | null
}

export interface ItemUpdatePayload {
  name?: string
  notes?: string
  merchant_name?: string
  merchant_address?: string
  transaction_date?: string
  transaction_time?: string
  total_amount?: number
  line_items?: LineItem[]
}

/** Result of an upload before it's been reviewed and saved — nothing is in the database yet. */
export interface ItemDraft {
  draft_id: string
  original_filename: string
  status: 'extracted' | 'failed'
  merchant_name: string | null
  merchant_address: string | null
  transaction_date: string | null
  transaction_time: string | null
  total_amount: number | null
  line_items: LineItem[]
  error_message: string | null
}

interface ItemFieldsPayload {
  name: string
  notes: string
  merchant_name?: string
  merchant_address?: string
  transaction_date?: string
  transaction_time?: string
  total_amount?: number
  line_items?: LineItem[]
}

export interface ItemConfirmPayload extends ItemFieldsPayload {
  draft_id: string
  original_filename: string
}

export type ItemCreatePayload = ItemFieldsPayload

interface ItemsContextValue {
  items: Item[]
  loading: boolean
  uploadDraft: (file: File) => Promise<ItemDraft>
  confirmDraft: (payload: ItemConfirmPayload) => Promise<Item>
  discardDraft: (draftId: string) => Promise<void>
  draftFileUrl: (draftId: string) => string
  addItem: (item: ItemCreatePayload) => Promise<Item>
  updateItem: (id: string, updates: ItemUpdatePayload) => Promise<Item>
  removeItem: (id: string) => Promise<void>
  fileUrl: (id: string) => string
}

const ItemsContext = createContext<ItemsContextValue | undefined>(undefined)

async function parseJson(response: Response) {
  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Request failed (${response.status}): ${body}`)
  }
  return response.json()
}

export function ItemsProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)

  async function refresh() {
    const response = await fetch(`${API_URL}/items/`, { credentials: 'include' })
    const data: Item[] = await parseJson(response)
    setItems(data)
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false))
  }, [])

  async function uploadDraft(file: File): Promise<ItemDraft> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch(`${API_URL}/items/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })
    return parseJson(response)
  }

  async function confirmDraft(payload: ItemConfirmPayload): Promise<Item> {
    const response = await fetch(`${API_URL}/items/confirm`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const created: Item = await parseJson(response)
    setItems(prev => [created, ...prev])
    return created
  }

  async function discardDraft(draftId: string): Promise<void> {
    const response = await fetch(`${API_URL}/items/draft/${draftId}`, {
      method: 'DELETE',
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`)
    }
  }

  function draftFileUrl(draftId: string): string {
    return `${API_URL}/items/draft/${draftId}/file`
  }

  async function addItem(item: ItemCreatePayload): Promise<Item> {
    const response = await fetch(`${API_URL}/items/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item),
    })
    const created: Item = await parseJson(response)
    setItems(prev => [created, ...prev])
    return created
  }

  async function updateItem(id: string, updates: ItemUpdatePayload): Promise<Item> {
    const response = await fetch(`${API_URL}/items/${id}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    })
    const updated: Item = await parseJson(response)
    setItems(prev => prev.map(item => (item.id === id ? updated : item)))
    return updated
  }

  async function removeItem(id: string): Promise<void> {
    const response = await fetch(`${API_URL}/items/${id}`, {
      method: 'DELETE',
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`)
    }
    setItems(prev => prev.filter(item => item.id !== id))
  }

  function fileUrl(id: string): string {
    return `${API_URL}/items/${id}/file`
  }

  return (
    <ItemsContext.Provider
      value={{
        items,
        loading,
        uploadDraft,
        confirmDraft,
        discardDraft,
        draftFileUrl,
        addItem,
        updateItem,
        removeItem,
        fileUrl,
      }}
    >
      {children}
    </ItemsContext.Provider>
  )
}

export function useItems() {
  const context = useContext(ItemsContext)
  if (!context) {
    throw new Error('useItems must be used within an ItemsProvider')
  }
  return context
}
