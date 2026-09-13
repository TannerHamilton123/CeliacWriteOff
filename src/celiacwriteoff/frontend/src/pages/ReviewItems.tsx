import { useState } from 'react'
import LineItemsTable from '../components/LineItemsTable'
import { useItems, type Item, type ItemUpdatePayload, type LineItem } from '../context/ItemsContext'
import './Pages.css'

interface Draft {
  name: string
  notes: string
  merchant_name: string
  merchant_address: string
  transaction_date: string
  transaction_time: string
  total_amount: string
  lineItems: LineItem[]
}

function draftFromItem(item: Item): Draft {
  return {
    name: item.name,
    notes: item.notes,
    merchant_name: item.merchant_name ?? '',
    merchant_address: item.merchant_address ?? '',
    transaction_date: item.transaction_date ?? '',
    transaction_time: item.transaction_time ?? '',
    total_amount: item.total_amount != null ? String(item.total_amount) : '',
    lineItems: item.line_items,
  }
}

function ReviewItems() {
  const { items, loading, updateItem, removeItem, fileUrl } = useItems()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  function startEditing(item: Item) {
    setEditingId(item.id)
    setDraft(draftFromItem(item))
  }

  function cancelEditing() {
    setEditingId(null)
    setDraft(null)
  }

  async function saveEditing(item: Item) {
    if (!draft) return
    const amount = parseFloat(draft.total_amount)
    const updates: ItemUpdatePayload = {
      name: draft.name.trim(),
      notes: draft.notes.trim(),
      merchant_name: draft.merchant_name.trim(),
      merchant_address: draft.merchant_address.trim(),
      transaction_date: draft.transaction_date.trim(),
      transaction_time: draft.transaction_time.trim(),
      line_items: draft.lineItems,
      ...(Number.isNaN(amount) ? {} : { total_amount: amount }),
    }
    await updateItem(item.id, updates)
    cancelEditing()
  }

  function toggleGlutenSubstitute(index: number) {
    if (!draft) return
    const lineItems = draft.lineItems.map((li, i) =>
      i === index ? { ...li, is_gluten_substitute: !li.is_gluten_substitute } : li,
    )
    setDraft({ ...draft, lineItems })
  }

  async function handleDelete(id: string) {
    setBusyId(id)
    try {
      await removeItem(id)
    } finally {
      setBusyId(null)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Review Items</h1>
        <p>Loading…</p>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>Review Items</h1>

      {items.length === 0 && <p>No items yet. Add some from the Add Items page.</p>}

      <ul className="item-list">
        {items.map(item => (
          <li key={item.id} className="item-row">
            {editingId === item.id && draft ? (
              <div className="manual-entry">
                <input
                  type="text"
                  placeholder="Item name"
                  value={draft.name}
                  onChange={e => setDraft({ ...draft, name: e.target.value })}
                />
                <textarea
                  rows={3}
                  placeholder="Notes"
                  value={draft.notes}
                  onChange={e => setDraft({ ...draft, notes: e.target.value })}
                />
                <div className="item-fields">
                  <label>
                    Merchant
                    <input
                      type="text"
                      value={draft.merchant_name}
                      onChange={e => setDraft({ ...draft, merchant_name: e.target.value })}
                    />
                  </label>
                  <label>
                    Address
                    <input
                      type="text"
                      value={draft.merchant_address}
                      onChange={e => setDraft({ ...draft, merchant_address: e.target.value })}
                    />
                  </label>
                  <label>
                    Date
                    <input
                      type="text"
                      value={draft.transaction_date}
                      onChange={e => setDraft({ ...draft, transaction_date: e.target.value })}
                    />
                  </label>
                  <label>
                    Time
                    <input
                      type="text"
                      value={draft.transaction_time}
                      onChange={e => setDraft({ ...draft, transaction_time: e.target.value })}
                    />
                  </label>
                  <label>
                    Total amount
                    <input
                      type="number"
                      step="0.01"
                      value={draft.total_amount}
                      onChange={e => setDraft({ ...draft, total_amount: e.target.value })}
                    />
                  </label>
                </div>
                <LineItemsTable
                  lineItems={draft.lineItems}
                  onToggleGlutenSubstitute={toggleGlutenSubstitute}
                />
                <div className="item-actions">
                  <button type="button" className="counter" onClick={() => saveEditing(item)}>
                    Save
                  </button>
                  <button type="button" className="counter" onClick={cancelEditing}>
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="item-body">
                  {item.source === 'file' && (
                    <img
                      className="item-preview"
                      src={fileUrl(item.id)}
                      alt={item.original_filename ?? 'Receipt'}
                    />
                  )}
                  <div className="item-info">
                    <span className={`item-source-badge item-source-badge-${item.source}`}>
                      {item.source === 'manual' ? 'Manual entry' : 'Receipt upload'}
                    </span>
                    <strong>{item.name || item.merchant_name || 'Untitled item'}</strong>
                    {item.merchant_address && <p>{item.merchant_address}</p>}
                    {(item.transaction_date || item.transaction_time) && (
                      <p>{[item.transaction_date, item.transaction_time].filter(Boolean).join(' ')}</p>
                    )}
                    {item.total_amount != null && <p>Total: ${item.total_amount.toFixed(2)}</p>}
                    {item.notes && <p>{item.notes}</p>}
                  </div>
                </div>
                <div className="item-actions">
                  <button type="button" className="counter" onClick={() => startEditing(item)}>
                    Edit
                  </button>
                  <button
                    type="button"
                    className="counter"
                    onClick={() => handleDelete(item.id)}
                    disabled={busyId === item.id}
                  >
                    Delete
                  </button>
                </div>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default ReviewItems
