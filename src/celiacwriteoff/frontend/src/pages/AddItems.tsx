import { useState } from 'react'
import LineItemsTable from '../components/LineItemsTable'
import {
  useItems,
  type ItemCreatePayload,
  type ItemConfirmPayload,
  type ItemDraft,
  type LineItem,
} from '../context/ItemsContext'
import './Pages.css'

type ReviewMode = { kind: 'draft'; draft: ItemDraft } | { kind: 'manual' }

interface ReviewForm {
  mode: ReviewMode
  name: string
  notes: string
  merchant_name: string
  merchant_address: string
  transaction_date: string
  transaction_time: string
  total_amount: string
  lineItems: LineItem[]
}

function formFromDraft(draft: ItemDraft): ReviewForm {
  return {
    mode: { kind: 'draft', draft },
    name: draft.merchant_name ?? '',
    notes: '',
    merchant_name: draft.merchant_name ?? '',
    merchant_address: draft.merchant_address ?? '',
    transaction_date: draft.transaction_date ?? '',
    transaction_time: draft.transaction_time ?? '',
    total_amount: draft.total_amount != null ? String(draft.total_amount) : '',
    lineItems: draft.line_items,
  }
}

function emptyManualForm(): ReviewForm {
  return {
    mode: { kind: 'manual' },
    name: '',
    notes: '',
    merchant_name: '',
    merchant_address: '',
    transaction_date: '',
    transaction_time: '',
    total_amount: '',
    lineItems: [],
  }
}

function AddItems() {
  const { addItem, uploadDraft, confirmDraft, discardDraft, draftFileUrl } = useItems()
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [queue, setQueue] = useState<File[]>([])
  const [current, setCurrent] = useState<ReviewForm | null>(null)
  const [processing, setProcessing] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  function handleFileSelection(event: React.ChangeEvent<HTMLInputElement>) {
    setSelectedFiles(Array.from(event.target.files ?? []))
    setUploadError(null)
  }

  async function processNext(remaining: File[]) {
    if (remaining.length === 0) {
      setQueue([])
      return
    }
    const [next, ...rest] = remaining
    setQueue(rest)
    setProcessing(true)
    setUploadError(null)
    try {
      const draft = await uploadDraft(next)
      setCurrent(formFromDraft(draft))
    } catch (err) {
      setUploadError(`${next.name}: ${err instanceof Error ? err.message : 'Upload failed'}`)
      await processNext(rest)
      return
    } finally {
      setProcessing(false)
    }
  }

  async function handleUpload() {
    const files = selectedFiles
    setSelectedFiles([])
    await processNext(files)
  }

  function startManualEntry() {
    setCurrent(emptyManualForm())
  }

  async function handleConfirm() {
    if (!current) return
    const amount = parseFloat(current.total_amount)
    const fields: ItemCreatePayload = {
      name: current.name.trim(),
      notes: current.notes.trim(),
      merchant_name: current.merchant_name.trim(),
      merchant_address: current.merchant_address.trim(),
      transaction_date: current.transaction_date.trim(),
      transaction_time: current.transaction_time.trim(),
      line_items: current.lineItems,
      ...(Number.isNaN(amount) ? {} : { total_amount: amount }),
    }

    if (current.mode.kind === 'draft') {
      const payload: ItemConfirmPayload = {
        draft_id: current.mode.draft.draft_id,
        original_filename: current.mode.draft.original_filename,
        ...fields,
      }
      await confirmDraft(payload)
      setCurrent(null)
      await processNext(queue)
    } else {
      await addItem(fields)
      setCurrent(null)
    }
  }

  function toggleGlutenSubstitute(index: number) {
    if (!current) return
    const lineItems = current.lineItems.map((li, i) =>
      i === index ? { ...li, is_gluten_substitute: !li.is_gluten_substitute } : li,
    )
    setCurrent({ ...current, lineItems })
  }

  async function handleDiscard() {
    if (!current) return
    if (current.mode.kind === 'draft') {
      await discardDraft(current.mode.draft.draft_id)
      setCurrent(null)
      await processNext(queue)
    } else {
      setCurrent(null)
    }
  }

  const isManual = current?.mode.kind === 'manual'

  return (
    <div className="page add-items-page">
      <h1>Add Items</h1>

      <div className="add-items-layout">
        <div className="add-items-left">
          <section className="panel">
            <h2>Upload files</h2>
            <input
              type="file"
              multiple
              accept="image/*"
              aria-label="Select receipt image files"
              onChange={handleFileSelection}
              disabled={processing}
            />
            {selectedFiles.length > 0 && (
              <ul className="file-list">
                {selectedFiles.map(file => (
                  <li key={file.name}>{file.name}</li>
                ))}
              </ul>
            )}
            {uploadError && <p className="error-text">{uploadError}</p>}
            <button
              type="button"
              className="counter"
              onClick={handleUpload}
              disabled={selectedFiles.length === 0 || processing}
            >
              {processing ? 'Processing receipt…' : 'Upload selected files'}
            </button>
            {queue.length > 0 && <p>{queue.length} more waiting…</p>}
          </section>

          <section className="panel">
            <h2>Manual entry</h2>
            <p>No receipt to scan? Fill in the same details by hand.</p>
            <button
              type="button"
              className="counter"
              onClick={startManualEntry}
              disabled={current !== null}
            >
              Add information manually
            </button>
          </section>
        </div>

        <div className="add-items-right">
          {processing && !current && (
            <section className="panel">
              <p>Reading receipt…</p>
            </section>
          )}

          {current && (
            <section className="panel">
              <h2>{isManual ? 'Add item manually' : 'Review before saving'}</h2>
              {current.mode.kind === 'draft' && (
                <img
                  className="item-preview"
                  src={draftFileUrl(current.mode.draft.draft_id)}
                  alt={current.mode.draft.original_filename}
                />
              )}
              {current.mode.kind === 'draft' &&
                current.mode.draft.status === 'failed' &&
                current.mode.draft.error_message && (
                  <p className="error-text">
                    Couldn't read this receipt automatically ({current.mode.draft.error_message}).
                    Fill in the fields below manually.
                  </p>
                )}
              <div className="manual-entry">
                <label>
                  Name
                  <input
                    type="text"
                    value={current.name}
                    onChange={e => setCurrent({ ...current, name: e.target.value })}
                  />
                </label>
                <label>
                  Notes
                  <textarea
                    rows={2}
                    value={current.notes}
                    onChange={e => setCurrent({ ...current, notes: e.target.value })}
                  />
                </label>
                <div className="item-fields">
                  <label>
                    Merchant
                    <input
                      type="text"
                      value={current.merchant_name}
                      onChange={e => setCurrent({ ...current, merchant_name: e.target.value })}
                    />
                  </label>
                  <label>
                    Address
                    <input
                      type="text"
                      value={current.merchant_address}
                      onChange={e => setCurrent({ ...current, merchant_address: e.target.value })}
                    />
                  </label>
                  <label>
                    Date
                    <input
                      type="text"
                      value={current.transaction_date}
                      onChange={e => setCurrent({ ...current, transaction_date: e.target.value })}
                    />
                  </label>
                  <label>
                    Time
                    <input
                      type="text"
                      value={current.transaction_time}
                      onChange={e => setCurrent({ ...current, transaction_time: e.target.value })}
                    />
                  </label>
                  <label>
                    Total amount
                    <input
                      type="number"
                      step="0.01"
                      value={current.total_amount}
                      onChange={e => setCurrent({ ...current, total_amount: e.target.value })}
                    />
                  </label>
                </div>
                <LineItemsTable
                  lineItems={current.lineItems}
                  onToggleGlutenSubstitute={toggleGlutenSubstitute}
                />
                <div className="item-actions">
                  <button type="button" className="counter" onClick={handleConfirm}>
                    Save
                  </button>
                  <button type="button" className="counter" onClick={handleDiscard}>
                    {isManual ? 'Cancel' : 'Discard'}
                  </button>
                </div>
              </div>
            </section>
          )}

          {!processing && !current && queue.length === 0 && (
            <section className="panel">
              <p>Upload a receipt or add an item manually to review its details here before saving.</p>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}

export default AddItems
